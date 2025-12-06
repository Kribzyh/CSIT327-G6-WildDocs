#!/usr/bin/env python
"""
Test script to verify core features:
1. Database connection
2. User/StudentAccount creation
3. Email sending (password reset)
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WildDocs.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import connection
from accounts.models import StudentAccount, DocumentType


def test_database_connection():
    """Test 1: Database connection"""
    print("\n" + "="*50)
    print("TEST 1: Database Connection")
    print("="*50)
    
    try:
        # Check which database is being used
        db_engine = settings.DATABASES['default']['ENGINE']
        print(f"Database Engine: {db_engine}")
        
        if 'sqlite' in db_engine:
            print("⚠️  Using SQLite (local fallback)")
            print("   To use Supabase, configure DATABASE_URL in .env")
        else:
            print("✅ Using PostgreSQL (likely Supabase)")
        
        # Test connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result[0] == 1:
                print("✅ Database connection successful!")
                return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_user_creation():
    """Test 2: User and StudentAccount creation"""
    print("\n" + "="*50)
    print("TEST 2: User & StudentAccount Creation")
    print("="*50)
    
    test_email = "test_user_12345@example.com"
    test_student_number = "99-9999-999"
    
    try:
        # Clean up any existing test user
        User.objects.filter(email=test_email).delete()
        StudentAccount.objects.filter(student_number=test_student_number).delete()
        
        # Create User
        user = User.objects.create_user(
            username=test_email,
            email=test_email,
            password="TestPassword123!",
            first_name="Test",
            last_name="User"
        )
        print(f"✅ User created: {user.username}")
        
        # Create StudentAccount
        student = StudentAccount.objects.create(
            user=user,
            student_number=test_student_number,
            first_name="Test",
            last_name="User",
            email=test_email,
            course="Computer Science",
            program="CCS",
            year_level=3
        )
        print(f"✅ StudentAccount created: {student.student_number}")
        
        # Verify data is saved
        saved_student = StudentAccount.objects.get(student_number=test_student_number)
        print(f"✅ Data verified in database:")
        print(f"   - Student Number: {saved_student.student_number}")
        print(f"   - Name: {saved_student.first_name} {saved_student.last_name}")
        print(f"   - Email: {saved_student.email}")
        print(f"   - Course: {saved_student.course}")
        print(f"   - Program: {saved_student.program}")
        
        # Clean up
        user.delete()  # This cascades to StudentAccount
        print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ User creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_email_configuration():
    """Test 3: Email configuration"""
    print("\n" + "="*50)
    print("TEST 3: Email Configuration")
    print("="*50)
    
    try:
        email_backend = settings.EMAIL_BACKEND
        print(f"Email Backend: {email_backend}")
        
        if 'mailjet' in email_backend.lower():
            print("✅ Using Mailjet HTTP API backend")
            api_key = getattr(settings, 'MAILJET_API_KEY', '')
            secret_key = getattr(settings, 'MAILJET_SECRET_KEY', '')
            
            if api_key and secret_key:
                print(f"✅ Mailjet API Key configured: {api_key[:8]}...")
                print(f"✅ Mailjet Secret Key configured: {secret_key[:8]}...")
            else:
                print("⚠️  Mailjet keys not configured in .env")
                print("   Add MAILJET_API_KEY and MAILJET_SECRET_KEY to .env")
                return False
        else:
            print(f"⚠️  Using: {email_backend}")
            print("   Mailjet not configured - check MAILJET_API_KEY/MAILJET_SECRET_KEY in .env")
        
        print(f"Default From Email: {settings.DEFAULT_FROM_EMAIL}")
        return True
        
    except Exception as e:
        print(f"❌ Email configuration check failed: {e}")
        return False


def test_send_email(recipient_email=None):
    """Test 4: Actually send a test email (optional)"""
    print("\n" + "="*50)
    print("TEST 4: Send Test Email")
    print("="*50)
    
    if not recipient_email:
        print("⏭️  Skipping email send test (no recipient provided)")
        print("   Run with: python test_features.py your@email.com")
        return None
    
    try:
        send_mail(
            subject='WildDocs Test Email',
            message='This is a test email from WildDocs to verify email functionality is working.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        print(f"✅ Test email sent to: {recipient_email}")
        print("   Check your inbox (and spam folder)!")
        return True
        
    except Exception as e:
        print(f"❌ Email send failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_supabase_connection():
    """Test 5: Supabase Auth connection (if configured)"""
    print("\n" + "="*50)
    print("TEST 5: Supabase Connection")
    print("="*50)
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("⚠️  Supabase not configured")
        print("   Add SUPABASE_URL and SUPABASE_SERVICE_KEY to .env")
        return None
    
    try:
        from services.supabase_client import check_user_exists
        
        # Test API connection by checking if a dummy user exists
        exists, result = check_user_exists("nonexistent@test.com")
        
        if isinstance(result, str) and 'Error' in result:
            print(f"❌ Supabase connection error: {result}")
            return False
        else:
            print(f"✅ Supabase Auth API connected!")
            print(f"   URL: {supabase_url}")
            return True
            
    except Exception as e:
        print(f"❌ Supabase test failed: {e}")
        return False


def main():
    print("\n" + "🔍 WILDDOCS FEATURE TESTS 🔍".center(50))
    
    results = {}
    
    # Run tests
    results['database'] = test_database_connection()
    results['user_creation'] = test_user_creation()
    results['email_config'] = test_email_configuration()
    results['supabase'] = test_supabase_connection()
    
    # Optional: send test email if recipient provided
    if len(sys.argv) > 1:
        results['email_send'] = test_send_email(sys.argv[1])
    else:
        results['email_send'] = test_send_email()
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⏭️  SKIP"
        print(f"{test_name}: {status}")
    
    print("\n" + "="*50)
    print("To test with Supabase, add these to .env:")
    print("  SUPABASE_URL=https://your-project.supabase.co")
    print("  SUPABASE_KEY=your-anon-key")
    print("  SUPABASE_SERVICE_KEY=your-service-role-key")
    print("  DATABASE_URL=postgresql://...")
    print("")
    print("To test email sending:")
    print("  python test_features.py your@email.com")
    print("="*50)


if __name__ == '__main__':
    main()
