import os
import sys
import uuid

# Ensure project root is in sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WildDocs.settings')
import django
django.setup()

from django.conf import settings
from supabase import create_client

def main():
    try:
        sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    except Exception as e:
        print('ERROR creating supabase client:', e)
        return

    bucket = getattr(settings, 'SUPABASE_REQUIREMENTS_BUCKET', 'requirements')
    prefix = 'test_uploads/'
    key = prefix + 'test-' + uuid.uuid4().hex + '.txt'
    data = b'hello-supabase-test'
    try:
        sb.storage.from_(bucket).upload(key, data, {'content-type': 'text/plain'})
        print('UPLOAD_OK', key)
    except Exception as e:
        print('UPLOAD_ERROR', str(e))

    try:
        items = sb.storage.from_(bucket).list(prefix)
        print('LIST:', items)
    except Exception as e:
        print('LIST_ERROR', str(e))

if __name__ == '__main__':
    main()
