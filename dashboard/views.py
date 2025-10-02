from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from accounts.models import StudentAccount
from accounts.forms import StudentProfileForm

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
                request.session['student_name'] = user.full_name
                request.session['student_id_number'] = user.student_id
                request.session['student_course'] = user.course
                request.session['student_year_level'] = user.year_level
                
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid password')
        except StudentAccount.DoesNotExist:
            messages.error(request, 'User does not exist')
    return render(request, 'login.html')

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
        course = request.POST.get('course')
        year_level = request.POST.get('year_level')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'register.html')
        
        # Check if student ID already exists
        if StudentAccount.objects.filter(student_id=student_id).exists():
            messages.error(request, 'Student ID already registered')
            return render(request, 'register.html')
        
        # Check if email already exists
        if StudentAccount.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'register.html')
        
        try:
            # Auto-determine program based on course
            from accounts.forms import StudentProfileForm
            program = StudentProfileForm.get_program_from_course(course)
            
            # Create new student account - use student_id as username
            student = StudentAccount.objects.create(
                first_name=first_name,
                last_name=last_name,
                student_id=student_id,
                email=email,
                username=student_id,
                password=make_password(password),
                course=course,
                program=program,  # Auto-determined
                year_level=int(year_level) if year_level else None,
            )
            
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, 'An error occurred while creating your account. Please try again.')
    
    return render(request, 'register.html')

def logout(request):
    request.session.flush()
    return redirect('home')

def dashboard(request):
    # Check if user is logged in
    if not request.session.get('student_id'):
        return redirect('login')  # Redirect to login instead of setting test data
    
    # Get student information from database
    try:
        student_id = request.session.get('student_id')
        student = StudentAccount.objects.get(id=student_id)
        
        # Determine college from program
        college = student.program if student.program else 'Computer Studies'
        
        context = {
            'student_name': student.full_name,
            'student_id_number': student.student_id,
            'student_course': student.course or 'BSIT',
            'student_college': college,
            'student_year': f"Year {student.year_level or 1} of 4",
            'student_status': 'Regular Student',
            'student': student,
        }
    except StudentAccount.DoesNotExist:
        # If student not found, clear session and redirect to login
        request.session.flush()
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')
    
    return render(request, 'dashboard.html', context)

def edit_profile(request):
    # Check if user is logged in
    if not request.session.get('student_id'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('login')
    
    try:
        student_id = request.session.get('student_id')
        student = StudentAccount.objects.get(id=student_id)
    except StudentAccount.DoesNotExist:
        messages.error(request, 'Student account not found.')
        return redirect('login')
    
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            # Update session data
            request.session['student_name'] = student.full_name
            request.session['student_course'] = student.course
            request.session['student_year_level'] = student.year_level
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentProfileForm(instance=student)
    
    context = {
        'form': form,
        'student': student,
    }
    return render(request, 'edit_profile.html', context)