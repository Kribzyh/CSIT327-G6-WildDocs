from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from services.supabase_client import create_user_admin

class Command(BaseCommand):
    help = 'Migrate all Django users to Supabase Auth (creates Supabase users for each Django user if not present)'

    def handle(self, *args, **options):
        users = User.objects.all()
        created = 0
        skipped = 0
        for user in users:
            email = user.email
            password = User.objects.make_random_password()
            user_metadata = {
                "student_number": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
            resp, err = create_user_admin(email, password, user_metadata)
            if err == "User already exists":
                self.stdout.write(self.style.WARNING(f"Skipped (already exists): {email}"))
                skipped += 1
            elif err:
                self.stdout.write(self.style.ERROR(f"Error for {email}: {err}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Created Supabase user: {email}"))
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Skipped: {skipped}, Total: {users.count()}"))
