from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .models import StudentAccount


def login(request):
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        student_number = request.POST.get('student_id')
        password = request.POST.get('password')

        # Authenticate using username (which stores student_number)
        user = authenticate(request, username=student_number, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid student number or password.')

    return render(request, 'pages/login.html')


def register(request):
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        student_number = request.POST.get('student_id')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        course = request.POST.get('course')
        year_level = request.POST.get('year_level')

        # Password validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'pages/register.html')

        # Uniqueness checks
        if User.objects.filter(username=student_number).exists():
            messages.error(request, 'Student number already registered.')
            return render(request, 'pages/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'pages/register.html')

        # Create user (using student_number as username)
        user = User.objects.create(
            username=student_number,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=make_password(password)
        )

        # Create linked student profile
        StudentAccount.objects.create(
            user=user,
            student_number=student_number,
            course=course,
            year_level=year_level
        )

        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('login')

    return render(request, 'pages/register.html')


def logout(request):
    auth_logout(request)
    return redirect('login')