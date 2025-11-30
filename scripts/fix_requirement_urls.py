import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','WildDocs.settings')
import django
django.setup()
from django.conf import settings
from request.models import RequirementUpload

bucket = getattr(settings, 'SUPABASE_REQUIREMENTS_BUCKET', 'requirements')
rows = RequirementUpload.objects.filter(request_id=41)
print('Before:', list(rows.values('id','supabase_id','file_url')))
count = 0
for r in rows:
    sid = r.supabase_id
    if not sid:
        continue
    new_url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/public/{bucket}/{sid}"
    r.file_url = new_url
    r.save()
    count += 1
print('Updated', count)
print('After:', list(RequirementUpload.objects.filter(request_id=41).values('id','supabase_id','file_url')))
