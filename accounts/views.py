from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.utils import timezone
import re  # Added missing import
from services.supabase_client import create_user_admin, delete_user_admin, check_user_exists

from .models import StudentAccount, AdminAccount
from .forms import StudentProfileForm
from services.supabase_client import create_user_admin, delete_user_admin
from django.views.decorators.cache import never_cache

@never_cache
def login(request):
    # --- Already logged in ---
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        elif hasattr(request.user, 'studentaccount'):
            return redirect('dashboard')
        return redirect('dashboard')

    # --- Login attempt ---
    if request.method == 'POST':
        identifier = request.POST.get('student_id')  # can be email or student_number
        password = request.POST.get('password')
        user = None

        # --- If identifier is an email ---
        if '@' in identifier:
            try:
                # Find user by email
                user_obj = User.objects.get(email=identifier)
            except User.DoesNotExist:
                messages.error(request, 'This email is not registered.')
                return render(request, 'login.html')

            # Authenticate using the found username
            user = authenticate(request, username=user_obj.username, password=password)

            # If authentication fails
            if user is None:
                messages.error(request, 'Invalid password. Please try again.')
                return render(request, 'login.html')

            # --- Check if staff/admin ---
            if user.is_staff:
                try:
                    admin_acc = AdminAccount.objects.get(user=user)
                    admin_acc.last_login_at = timezone.now()
                    admin_acc.save()
                    messages.success(request, f"Welcome back, {admin_acc.full_name}!")
                    auth_login(request, user)
                    return redirect('admin_dashboard')
                except AdminAccount.DoesNotExist:
                    messages.error(request, 'Admin account not found for this user.')
                    return render(request, 'login.html')

            # --- Otherwise, treat as student ---
            else:
                try:
                    student_acc = StudentAccount.objects.get(user=user)
                    # Optional auto-program update
                    if student_acc.program == "Other" and student_acc.course:
                        try:
                            student_acc.program = StudentProfileForm.get_program_from_course(student_acc.course)
                            student_acc.save()
                        except Exception:
                            pass
                    messages.success(request, f"Welcome back, {student_acc.first_name} {student_acc.last_name}!")
                    auth_login(request, user)
                    return redirect('dashboard')
                except StudentAccount.DoesNotExist:
                    messages.error(request, 'Student account not found for this user.')
                    return render(request, 'login.html')

        # --- Otherwise, identifier is a student number ---
        else:
            try:
                student_account = StudentAccount.objects.get(student_number=identifier)
                user = authenticate(request, username=student_account.user.username, password=password)
                if user is not None:
                    auth_login(request, user)
                    messages.success(request, f"Welcome back, {student_account.first_name} {student_account.last_name}!")
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Invalid password. Please try again.')
            except StudentAccount.DoesNotExist:
                messages.error(request, 'This student ID does not exist in our records.')

    # --- Render login page ---
    return render(request, 'login.html')

@never_cache
def register(request):
    if request.user.is_authenticated:
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('dashboard')

    if request.method == 'POST':
        student_number = request.POST.get('student_id')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        course = request.POST.get('course')
        year_level = request.POST.get('year_level')

        # Step 1: Validate required fields
        if not all([student_number, email, password, first_name, last_name]):
            messages.error(request, "All fields are required.")
            return redirect('register')

        # Step 2: Validate email format
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            messages.error(request, "Please enter a valid email address.")
            return redirect('register')

        # Step 3: Validate password strength
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return redirect('register')

        # Step 4: Default year_level to 1 if empty or invalid
        try:
            year_level = int(year_level) if year_level else 1
        except ValueError:
            year_level = 1

        # Step 5: Check if student_number or email already exists in Django
        if User.objects.filter(username=student_number).exists():
            messages.error(request, "A user with that Student ID already exists.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with that email already exists.")
            return redirect('register')

        # NEW: Check if user actually exists in Supabase
        user_exists, existing_user = check_user_exists(email)
        if user_exists:
            print(f"User found in Supabase: {existing_user}")  # Debug
            messages.error(request, "A user with that email address has already been registered in our system.")
            return redirect('register')

        # Step 6: Create user in Supabase Auth first
        user_metadata = {
            "student_number": student_number,
            "first_name": first_name,
            "last_name": last_name,
            "course": course if course else '',
            "year_level": year_level
        }
        
        print(f"Creating Supabase user: {email}")
        
        supa_resp, supa_err = create_user_admin(email, password, user_metadata)
        
        if supa_err:
            print(f"Supabase error: {supa_err}")
            
            # If we get "already exists" error but our check didn't find it,
            # there might be a timing issue or the user is in a different state
            if "already exists" in supa_err.lower() or "already registered" in supa_err.lower():
                # Try to get the specific user
                user_exists, existing_user = check_user_exists(email)
                if user_exists:
                    messages.error(request, "This email is already registered. Please use a different email or try logging in.")
                else:
                    # User might be in "invited" state or other edge case
                    messages.error(request, "This email appears to be in our system. Please try logging in or use a different email address.")
            elif "password" in supa_err.lower():
                messages.error(request, "Password does not meet requirements.")
            else:
                messages.error(request, f"Registration error: {supa_err}")
            return redirect('register')

        # Continue with the rest of your registration logic...
        supa_uid = None
        if supa_resp and isinstance(supa_resp, dict):
            supa_uid = supa_resp.get('id')
            print(f"Created Supabase user with ID: {supa_uid}")

        try:
            # Step 7: Create the User in Django
            user = User.objects.create_user(
                username=student_number,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Step 8: Create linked StudentAccount
            program = StudentProfileForm.get_program_from_course(course if course else '')
            StudentAccount.objects.create(
                user=user,
                student_number=student_number,
                first_name=first_name,
                last_name=last_name,
                email=email,
                course=course if course else '',
                program=program,
                year_level=year_level
            )

            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')

        except Exception as e:
            # Rollback: delete Supabase user if Django user creation fails
            if supa_uid:
                print(f"Rollback: deleting Supabase user {supa_uid}")
                success, delete_err = delete_user_admin(supa_uid)
                if not success:
                    print(f"Failed to delete Supabase user during rollback: {delete_err}")
            
            messages.error(request, f"Registration failed: {str(e)}")
            return redirect('register')

    return render(request, 'register.html')

@never_cache
def logout(request):
    auth_logout(request)
    request.session.flush()
    return redirect('login')