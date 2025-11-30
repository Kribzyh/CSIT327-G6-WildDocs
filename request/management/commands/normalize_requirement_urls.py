from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from request.models import RequirementUpload

class Command(BaseCommand):
    help = 'Normalize RequirementUpload.file_url to use direct public object URL without trailing query for a request (use --request id to limit)'

    def add_arguments(self, parser):
        parser.add_argument('--request', dest='request_id', type=int, help='Limit to this request id')

    def handle(self, *args, **options):
        request_id = options.get('request_id')
        qs = RequirementUpload.objects.all()
        if request_id:
            qs = qs.filter(request_id=request_id)
        bucket = getattr(settings, 'SUPABASE_REQUIREMENTS_BUCKET', 'requirements')
        updated = 0
        for r in qs:
            sid = (r.supabase_id or '').lstrip('/')
            if not sid:
                continue
            new_url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/public/{bucket}/{sid}"
            if r.file_url != new_url:
                r.file_url = new_url
                r.save()
                updated += 1
        self.stdout.write(self.style.SUCCESS(f'Updated {updated} rows'))
