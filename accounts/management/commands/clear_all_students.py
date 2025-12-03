"""
Management command to remove all student accounts and their related data
from both Django database and Supabase storage.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from accounts.models import StudentAccount, Request, Notification
from request.models import RequirementUpload, PaymentUpload
from supabase import create_client
import requests


class Command(BaseCommand):
    help = 'Remove all student accounts and their related data from Django and Supabase'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion (required to actually delete data)',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                'This will DELETE ALL student accounts and their data!\n'
                'Run with --confirm to proceed.'
            ))
            
            # Show counts
            student_count = StudentAccount.objects.count()
            request_count = Request.objects.count()
            req_upload_count = RequirementUpload.objects.count()
            pay_upload_count = PaymentUpload.objects.count()
            notification_count = Notification.objects.count()
            
            self.stdout.write(f'\nData to be deleted:')
            self.stdout.write(f'  - {student_count} student accounts')
            self.stdout.write(f'  - {request_count} requests')
            self.stdout.write(f'  - {req_upload_count} requirement uploads')
            self.stdout.write(f'  - {pay_upload_count} payment uploads')
            self.stdout.write(f'  - {notification_count} notifications')
            return

        self.stdout.write(self.style.WARNING('Starting deletion process...'))

        # Get Supabase client
        supabase_url = getattr(settings, 'SUPABASE_URL', None)
        supabase_key = getattr(settings, 'SUPABASE_SERVICE_KEY', None)
        
        if supabase_url and supabase_key:
            supabase = create_client(supabase_url, supabase_key)
            
            # Delete files from Supabase storage buckets
            self._clear_bucket(supabase, 'requirements', 'Requirement files')
            self._clear_bucket(supabase, 'payments', 'Payment files')
            self._clear_bucket(supabase, 'profile-pictures', 'Profile pictures')
            
            # Delete users from Supabase Auth
            self._delete_supabase_auth_users(supabase_url, supabase_key)
        else:
            self.stdout.write(self.style.WARNING('Supabase not configured, skipping storage cleanup'))

        # Delete from Django database (order matters due to foreign keys)
        self.stdout.write('Deleting notifications...')
        notification_count = Notification.objects.count()
        Notification.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'  Deleted {notification_count} notifications'))

        self.stdout.write('Deleting requirement uploads...')
        req_count = RequirementUpload.objects.count()
        RequirementUpload.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'  Deleted {req_count} requirement uploads'))

        self.stdout.write('Deleting payment uploads...')
        pay_count = PaymentUpload.objects.count()
        PaymentUpload.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'  Deleted {pay_count} payment uploads'))

        self.stdout.write('Deleting requests...')
        request_count = Request.objects.count()
        Request.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'  Deleted {request_count} requests'))

        self.stdout.write('Deleting student accounts...')
        students = StudentAccount.objects.select_related('user').all()
        student_count = students.count()
        
        # Get user IDs before deleting students
        user_ids = list(students.values_list('user_id', flat=True))
        
        # Delete student accounts
        StudentAccount.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'  Deleted {student_count} student accounts'))

        # Delete associated Django users (non-staff only)
        self.stdout.write('Deleting Django user accounts...')
        deleted_users = User.objects.filter(id__in=user_ids, is_staff=False).delete()
        self.stdout.write(self.style.SUCCESS(f'  Deleted {deleted_users[0]} user accounts'))

        self.stdout.write(self.style.SUCCESS('\n✓ All student data has been removed!'))

    def _clear_bucket(self, supabase, bucket_name, description):
        """Clear all files from a Supabase storage bucket"""
        self.stdout.write(f'Clearing {description} from "{bucket_name}" bucket...')
        try:
            # List all files in the bucket
            files = supabase.storage.from_(bucket_name).list()
            
            if not files:
                self.stdout.write(f'  No files found in {bucket_name}')
                return
            
            deleted_count = 0
            for item in files:
                name = item.get('name', '')
                if not name:
                    continue
                    
                # Check if it's a folder (has nested files)
                if item.get('id') is None:
                    # It's a folder, list its contents
                    try:
                        folder_files = supabase.storage.from_(bucket_name).list(name)
                        if folder_files:
                            paths_to_delete = [f"{name}/{f['name']}" for f in folder_files if f.get('name')]
                            if paths_to_delete:
                                supabase.storage.from_(bucket_name).remove(paths_to_delete)
                                deleted_count += len(paths_to_delete)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  Error clearing folder {name}: {e}'))
                else:
                    # It's a file
                    try:
                        supabase.storage.from_(bucket_name).remove([name])
                        deleted_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  Error deleting {name}: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'  Deleted {deleted_count} files from {bucket_name}'))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  Error accessing bucket "{bucket_name}": {e}'))

    def _delete_supabase_auth_users(self, supabase_url, supabase_key):
        """Delete all non-admin users from Supabase Auth"""
        self.stdout.write('Deleting users from Supabase Auth...')
        
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
        }
        
        try:
            # Get all users
            url = f"{supabase_url}/auth/v1/admin/users"
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            users_data = resp.json()
            
            users = users_data.get('users', [])
            deleted_count = 0
            
            for user in users:
                user_id = user.get('id')
                email = user.get('email', '')
                
                # Skip admin users (you can customize this check)
                if email and ('admin' in email.lower() or 'staff' in email.lower()):
                    self.stdout.write(f'  Skipping admin user: {email}')
                    continue
                
                if user_id:
                    try:
                        delete_url = f"{supabase_url}/auth/v1/admin/users/{user_id}"
                        del_resp = requests.delete(delete_url, headers=headers, timeout=10)
                        if del_resp.status_code == 204:
                            deleted_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  Error deleting user {email}: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'  Deleted {deleted_count} users from Supabase Auth'))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  Error accessing Supabase Auth: {e}'))
