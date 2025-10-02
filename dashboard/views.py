from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.models import StudentAccount
from accounts.forms import StudentProfileForm

def dashboard(request):
    # Check if user is logged in
    if not request.session.get('student_id'):
        return redirect('login')
    
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