from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.utils import timezone

from .models import StudentAccount, AdminAccount
from .forms import StudentProfileForm
from services.supabase_client import create_user_admin, delete_user_admin
from django.views.decorators.cache import never_cache





@never_cache
def login(request):
    # --- Already logged in ---
    if request.user.is_authenticated:
        if hasattr(request.user, 'adminaccount'):
            return redirect('admin_dashboard')
        elif hasattr(request.user, 'studentaccount'):
            return redirect('dashboard')
        return redirect('dashboard')

    # --- Login attempt ---
    if request.method == 'POST':
        identifier = request.POST.get('student_id')  # student_number or email
        password = request.POST.get('password')
        user = None

        # --- Check if email (staff login) ---
        if '@' in identifier:
            try:
                admin_account = AdminAccount.objects.get(user__email=identifier, is_active=True)
                user = authenticate(request, username=admin_account.user.username, password=password)
            except AdminAccount.DoesNotExist:
                user = None

        # --- Otherwise, treat as student login ---
        else:
            try:
                student_account = StudentAccount.objects.get(student_number=identifier)
                user = authenticate(request, username=student_account.user.username, password=password)
            except StudentAccount.DoesNotExist:
                user = None

        # --- Handle successful login ---
        if user is not None:
            auth_login(request, user)

            # --- If Admin ---
            if hasattr(user, 'adminaccount'):
                admin_acc = user.adminaccount
                admin_acc.last_login_at = timezone.now()
                admin_acc.save()
                messages.success(request, f"Welcome back, {admin_acc.full_name}!")
                return redirect('admin_dashboard')

            # --- If Student ---
            elif hasattr(user, 'studentaccount'):
                student_acc = user.studentaccount

                # Auto-update program field if needed
                if student_acc.program == "Other" and student_acc.course:
                    try:
                        student_acc.program = StudentProfileForm.get_program_from_course(student_acc.course)
                        student_acc.save()
                    except Exception:
                        pass

                messages.success(request, f"Welcome back, {student_acc.first_name} {student_acc.last_name}!")
                return redirect('dashboard')

            # --- Fallback (should rarely happen) ---
            messages.warning(request, "Account type not recognized.")
            return redirect('dashboard')

        # --- Invalid login ---
        else:
            messages.error(request, 'Invalid student ID/email or password.')

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

        # Step 2: Default year_level to 1 if empty or invalid
        try:
            year_level = int(year_level) if year_level else 1
        except ValueError:
            year_level = 1

        # Step 3: Check if student_number or email already exists
        if User.objects.filter(username=student_number).exists():
            messages.error(request, "A user with that Student ID already exists.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with that email already exists.")
            return redirect('register')

        # Step 4: Create user in Supabase Auth first
        user_metadata = {
            "student_number": student_number,
            "first_name": first_name,
            "last_name": last_name,
            "course": course if course else '',
            "year_level": year_level
        }
        supa_resp, supa_err = create_user_admin(email, password, user_metadata)
        if supa_err == "User already exists":
            messages.error(request, "A Supabase Auth user with that email already exists.")
            return redirect('register')
        elif supa_err:
            messages.error(request, f"Supabase error: {supa_err}")
            return redirect('register')

        supa_uid = supa_resp.get('id') if supa_resp else None

        try:
            # Step 5: Create the User in Django
            user = User.objects.create_user(
                username=student_number,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Step 6: Create linked StudentAccount
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
        except Exception as e:
            # Rollback: delete Supabase user if Django user creation fails
            if supa_uid:
                delete_user_admin(supa_uid)
            messages.error(request, f"Registration failed: {e}")
            return redirect('register')

        # Step 7: Log the user in and redirect
        auth_login(request, user)
        messages.success(request, f"Welcome, {first_name}!")
        return redirect('dashboard')

    return render(request, 'register.html')




@never_cache
def logout(request):
    auth_logout(request)
    return redirect('login')
