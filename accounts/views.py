from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from .models import StudentAccount
from .forms import StudentProfileForm
import requests
from django.conf import settings
from django.views.decorators.cache import never_cache





@never_cache
def login(request):
    if request.user.is_authenticated:
        # If there's a 'next' parameter, redirect there instead of dashboard
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('dashboard')

    if request.method == 'POST':
        student_number = request.POST.get('student_id')
        password = request.POST.get('password')

        user = authenticate(request, username=student_number, password=password)
        if user is not None:
            auth_login(request, user)
            
            # Auto-populate student info based on course if program is not set
            try:
                student_account = user.studentaccount
                if student_account.program == "Other" and student_account.course:
                    student_account.program = StudentProfileForm.get_program_from_course(student_account.course)
                    student_account.save()
            except StudentAccount.DoesNotExist:
                pass
            
            messages.success(request, 'Successfully logged in!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid student number or password.')

    return render(request, 'login.html')

@never_cache
def register(request):
    # If already authenticated, don't allow access to registration page
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

        # ✅ Step 1: Validate required fields
        if not all([student_number, email, password, first_name, last_name]):
            messages.error(request, "All fields are required.")
            return redirect('register')

        # ✅ Step 2: Default year_level to 1 if empty or invalid
        try:
            year_level = int(year_level) if year_level else 1
        except ValueError:
            year_level = 1

        # ✅ Step 3: Check if student_number or email already exists
        if User.objects.filter(username=student_number).exists():
            messages.error(request, "A user with that Student ID already exists.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with that email already exists.")
            return redirect('register')

        # ✅ Step 4: Create the User in Django
        user = User.objects.create_user(
            username=student_number,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # ✅ Step 4.5: Also create user in Supabase Auth
        user_metadata = {
            "student_number": student_number,
            "first_name": first_name,
            "last_name": last_name,
            "course": course if course else '',
            "year_level": year_level
        }
        
        # NOTE: Supabase integration removed in this branch. Registration will only create a local Django user.

        # ✅ Step 5: Create linked StudentAccount
        # Automatically determine program based on course
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

        # ✅ Step 6: Log the user in and redirect
        auth_login(request, user)
        messages.success(request, f"Welcome, {first_name}!")
        return redirect('dashboard')

    return render(request, 'register.html')



@never_cache
def logout(request):
    auth_logout(request)
    return redirect('login')

def create_supabase_user(email, password, user_metadata=None):
    url = f"{settings.SUPABASE_URL}/auth/v1/admin/users"
    headers = {
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"email": email, "password": password}
    if user_metadata:
        payload["user_metadata"] = user_metadata

    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()  # raises requests.HTTPError for 4xx/5xx
    return resp.json()