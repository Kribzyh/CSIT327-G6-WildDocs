from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import StudentAccount

def login(request):
    # Redirect to dashboard if already logged in
    if request.session.get('student_id'):
        return redirect('dashboard')

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        password = request.POST.get('password')

        try:
            user = StudentAccount.objects.get(student_id=student_id)
            if user.check_password(password):
                # Set session
                request.session['student_id'] = user.id
                request.session['student_id_number'] = user.student_id
                
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid password')
        except StudentAccount.DoesNotExist:
            messages.error(request, 'User does not exist')
    return render(request, 'pages/login.html')

def register(request):
    # Redirect to dashboard if already logged in
    if request.session.get('student_id'):
        return redirect('dashboard')

    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        student_id = request.POST.get('student_id')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        course = request.POST.get('course')
        
        # Validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'pages/register.html')
        
        # Check if student ID already exists
        if StudentAccount.objects.filter(student_id=student_id).exists():
            messages.error(request, 'Student ID already registered')
            return render(request, 'pages/register.html')
        
        # Check if email already exists
        if StudentAccount.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'pages/register.html')
        
        try:
            # Create new student account - use student_id as username
            student = StudentAccount.objects.create(
                first_name=first_name,
                last_name=last_name,
                student_id=student_id,
                email=email,
                username=student_id,  # Use student_id as username
                password=make_password(password),
                course=course
            )
            
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, 'An error occurred while creating your account. Please try again.')
    
    return render(request, 'pages/register.html')

def logout(request):
    request.session.flush()
    return redirect('login') 