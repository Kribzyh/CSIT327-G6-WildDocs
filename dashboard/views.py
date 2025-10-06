from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.models import StudentAccount
from accounts.forms import StudentProfileForm
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    try:
        student = StudentAccount.objects.get(user=request.user)
        student_name = str(student)
    except StudentAccount.DoesNotExist:
        student = None  # or redirect to registration step if needed
        
        
    context = {
        'student': student,
        'student_name': student_name,
    }
    
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