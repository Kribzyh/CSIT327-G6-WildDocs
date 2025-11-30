import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','WildDocs.settings')
import django
django.setup()
from accounts.models import Request
from request.models import RequirementUpload, PaymentUpload
try:
    r = Request.objects.get(id=41)
    print('Request', r.id)
    print(' status:', r.status)
    print(' requirements_submitted_at:', r.requirements_submitted_at)
    print(' payment_submitted_at:', r.payment_submitted_at)
    print('requirement uploads:', RequirementUpload.objects.filter(request=r).count())
    print('payment uploads:', PaymentUpload.objects.filter(request=r).count())
except Exception as e:
    print('Error:', e)
