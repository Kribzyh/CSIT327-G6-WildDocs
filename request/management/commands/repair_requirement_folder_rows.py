from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from request.models import RequirementUpload
from accounts.models import Request as DocRequest
from supabase import create_client
from urllib.parse import urljoin
import os

class Command(BaseCommand):
    help = 'Repair RequirementUpload rows that reference folders (e.g., supabase_id="41"). Creates proper rows for each file under the folder prefix.'

    def add_arguments(self, parser):
        parser.add_argument('--request', dest='request_id', type=int, help='Limit repair to this request id')

    def handle(self, *args, **options):
        supabase_url = getattr(settings, 'SUPABASE_URL', None)
        supabase_key = getattr(settings, 'SUPABASE_SERVICE_KEY', None) or getattr(settings, 'SUPABASE_KEY', None)
        bucket = getattr(settings, 'SUPABASE_REQUIREMENTS_BUCKET', 'requirements')

        if not supabase_url or not supabase_key:
            raise CommandError('Supabase config missing in settings.')

        client = create_client(supabase_url, supabase_key)

        request_id = options.get('request_id')

        # find candidate rows: supabase_id that seems like a folder (no slash or exactly equal to request id)
        qs = RequirementUpload.objects.all()
        candidates = []
        for ru in qs:
            sid = (ru.supabase_id or '').strip()
            # treat placeholder values like '41' or '41/' or where file_url endswith '?' as folder indicator
            if not sid:
                continue
            if sid.isdigit() or sid.rstrip('/').isdigit() or (ru.file_url and ru.file_url.rstrip().endswith('/') or ru.file_url.endswith('?')):
                if request_id and (ru.request_id != request_id):
                    continue
                candidates.append(ru)

        if not candidates:
            self.stdout.write(self.style.NOTICE('No folder-like RequirementUpload rows found.'))
            return

        created = 0
        removed = 0
        scanned = 0

        for ru in candidates:
            scanned += 1
            sid = ru.supabase_id.rstrip('/')
            if not sid:
                continue
            # determine request id from supabase_id or from ru.request
            try:
                rid = int(sid) if sid.isdigit() else ru.request_id
            except Exception:
                rid = ru.request_id
            try:
                req_obj = DocRequest.objects.get(id=rid)
            except DocRequest.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Skipping supabase_id={sid}: Request {rid} not found'))
                continue

            self.stdout.write(f'Processing folder-like supabase_id="{sid}" for request {rid}...')
            try:
                try:
                    listing = client.storage.from_(bucket).list(f"{sid}/")
                except TypeError:
                    listing = client.storage.from_(bucket).list(prefix=f"{sid}/")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error listing bucket prefix {sid}/: {e}'))
                continue

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

            if not items:
                self.stdout.write(self.style.WARNING(f'No objects found under prefix {sid}/'))
                continue

            for it in items:
                try:
                    name = None
                    if isinstance(it, dict):
                        name = it.get('name') or it.get('key')
                        metadata = it.get('metadata') or {}
                    else:
                        name = getattr(it, 'name', None) or getattr(it, 'key', None)
                        metadata = getattr(it, 'metadata', {}) or {}
                except Exception:
                    continue
                if not name:
                    continue
                # skip pseudo-folders
                if name.rstrip('/').endswith(sid) and name.rstrip('/') == sid:
                    continue
                # skip if exists
                exists = RequirementUpload.objects.filter(supabase_id=name).exists()
                if exists:
                    self.stdout.write(self.style.NOTICE(f'Skipping existing supabase_id={name}'))
                    continue

                # get public url
                try:
                    pub = client.storage.from_(bucket).get_public_url(name)
                    if isinstance(pub, dict):
                        pub_url = pub.get('publicUrl') or pub.get('public_url') or pub.get('publicURL') or str(pub)
                    else:
                        pub_url = str(pub)
                except Exception:
                    pub_url = ''

                file_name = name.split('/')[-1]
                ru_new = RequirementUpload.objects.create(
                    request=req_obj,
                    uploaded_by=None,
                    file_name=file_name,
                    file_url=pub_url,
                    supabase_id=name,
                    delete_url='',
                    content_type=metadata.get('mimetype') if isinstance(metadata, dict) else None,
                    file_size=metadata.get('size') if isinstance(metadata, dict) else None,
                    provider='supabase'
                )
                try:
                    ru_new.delete_url = reverse('delete_requirement_upload', args=[ru_new.id])
                    ru_new.save()
                except Exception:
                    pass
                created += 1

            # remove the placeholder folder row
            try:
                ru.delete()
                removed += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to remove placeholder row id={ru.id}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Repair complete: scanned={scanned}, created={created}, removed={removed}'))
