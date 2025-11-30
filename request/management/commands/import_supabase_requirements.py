from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.urls import reverse
from request.models import RequirementUpload
from accounts.models import Request as DocRequest
from supabase import create_client
import os


class Command(BaseCommand):
    help = 'Import existing files from Supabase requirements bucket into RequirementUpload rows. Use --request <id> to limit to one request.'

    def add_arguments(self, parser):
        parser.add_argument('--request', dest='request_id', type=int, help='Import only for this request id')

    def handle(self, *args, **options):
        supabase_url = getattr(settings, 'SUPABASE_URL', None)
        supabase_key = getattr(settings, 'SUPABASE_SERVICE_KEY', None) or getattr(settings, 'SUPABASE_KEY', None)
        bucket = getattr(settings, 'SUPABASE_REQUIREMENTS_BUCKET', 'requirements')

        if not supabase_url or not supabase_key:
            raise CommandError('Supabase URL or service key not configured in settings.')

        client = create_client(supabase_url, supabase_key)

        request_id = options.get('request_id')

        # Get full file list from bucket
        try:
            listing = client.storage.from_(bucket).list()
        except Exception as e:
            raise CommandError(f'Error listing bucket "{bucket}": {e}')

        items = []
        if isinstance(listing, dict) and 'data' in listing:
            items = listing.get('data') or []
        elif hasattr(listing, 'data'):
            items = getattr(listing, 'data') or []
        elif isinstance(listing, (list, tuple)):
            items = list(listing)
        else:
            try:
                items = list(listing)
            except Exception:
                items = []

        created = 0
        skipped = 0

        for it in items:
            try:
                name = None
                if isinstance(it, dict):
                    name = it.get('name') or it.get('key')
                else:
                    name = getattr(it, 'name', None) or getattr(it, 'key', None)
            except Exception:
                continue
            if not name:
                continue
            # Expect names like '<request_id>/filename' or include request id somewhere
            parts = name.split('/')
            if not parts:
                continue
            # find first numeric segment as potential request id
            possible_ids = [p for p in parts if p.isdigit()]
            if not possible_ids:
                continue
            rid = int(possible_ids[0])
            if request_id and rid != request_id:
                continue
            # confirm the request exists
            try:
                req_obj = DocRequest.objects.get(id=rid)
            except DocRequest.DoesNotExist:
                skipped += 1
                continue

            # Check if a RequirementUpload with this supabase_id exists
            exists = RequirementUpload.objects.filter(supabase_id=name).exists()
            if exists:
                skipped += 1
                continue

            # Build public URL
            try:
                pub = client.storage.from_(bucket).get_public_url(name)
                if isinstance(pub, dict):
                    pub_url = pub.get('publicUrl') or pub.get('public_url') or pub.get('publicURL') or str(pub)
                else:
                    pub_url = str(pub)
            except Exception:
                pub_url = ''

            file_name = parts[-1]
            ru = RequirementUpload.objects.create(
                request=req_obj,
                uploaded_by=None,
                file_name=file_name,
                file_url=pub_url,
                supabase_id=name,
                delete_url=reverse('delete_requirement_upload', args=[0]).replace('/0/', f'/{0}/'),
                content_type=None,
                file_size=(it.get('metadata', {}) or {}).get('size') if isinstance(it, dict) else None,
                provider='supabase'
            )
            # set delete_url to relative endpoint for now
            try:
                ru.delete_url = reverse('delete_requirement_upload', args=[ru.id])
                ru.save()
            except Exception:
                pass

            created += 1

        self.stdout.write(self.style.SUCCESS(f'Import complete: created={created}, skipped={skipped}, scanned={len(items)}'))
