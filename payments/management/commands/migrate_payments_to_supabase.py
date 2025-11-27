from django.core.management.base import BaseCommand
from django.conf import settings
import requests
from payments.models import Payment
from services.supabase_client import SUPABASE_URL, SUPABASE_SERVICE_KEY


class Command(BaseCommand):
    help = 'Migrate unsynced Payment records to Supabase REST table `payments`.'

    def handle(self, *args, **options):
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            self.stderr.write('Supabase settings not configured (SUPABASE_URL / SUPABASE_SERVICE_KEY).')
            return

        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation',
        }

        url = f"{SUPABASE_URL}/rest/v1/payments"

        queryset = Payment.objects.filter(supabase_id__isnull=True)
        total = queryset.count()
        if total == 0:
            self.stdout.write('No unsynced payments found.')
            return

        self.stdout.write(f'Found {total} unsynced payments. Starting migration...')

        for p in queryset:
            payload = {
                'reference': p.reference,
                'amount': float(p.amount),
                'currency': p.currency,
                'status': p.status,
                'metadata': p.metadata or {},
                'created_at': p.created_at.isoformat() if p.created_at else None,
            }

            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=15)
            except requests.RequestException as e:
                self.stderr.write(f'Network error migrating {p.reference}: {e}')
                continue

            if resp.status_code in (200, 201):
                try:
                    data = resp.json()
                    # Supabase returns a list when using return=representation
                    if isinstance(data, list) and len(data) > 0:
                        remote = data[0]
                    elif isinstance(data, dict):
                        remote = data
                    else:
                        remote = None

                    if remote and 'id' in remote:
                        p.supabase_id = str(remote['id'])
                        p.save(update_fields=['supabase_id'])
                        self.stdout.write(f'Migrated {p.reference} -> supabase id {p.supabase_id}')
                    else:
                        self.stderr.write(f'Inserted but could not read remote id for {p.reference}: {data}')
                except ValueError:
                    self.stderr.write(f'Invalid JSON response for {p.reference}: {resp.text}')
            else:
                self.stderr.write(f'Failed to insert {p.reference}: {resp.status_code} {resp.text}')
