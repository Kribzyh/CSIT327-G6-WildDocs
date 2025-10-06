from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from .models import StudentAccount





def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        student_number = request.POST.get('student_id')
        password = request.POST.get('password')

        user = authenticate(request, username=student_number, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid student number or password.')

    return render(request, 'login.html')

def register(request):
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

        # ✅ Step 4: Create the User
        user = User.objects.create_user(
            username=student_number,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # ✅ Step 5: Create linked StudentAccount
        StudentAccount.objects.create(
            user=user,
            student_number=student_number,
            first_name=first_name,
            last_name=last_name,
            email=email,
            course=course if course else '',
            year_level=year_level
        )

        # ✅ Step 6: Log the user in and redirect
        auth_login(request, user)
        messages.success(request, f"Welcome, {first_name}!")
        return redirect('dashboard')

    return render(request, 'register.html')


def logout(request):
    auth_logout(request)
    return redirect('login')