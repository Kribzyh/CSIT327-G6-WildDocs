from django.shortcuts import render, redirect
from django.contrib import messages
from .models import StudentAccount

def login(request):
    # Redirect to dashboard if already logged in
    if request.session.get('student_id'):
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = StudentAccount.objects.get(username=username)
            if user.check_password(password):
                # Set session
                request.session['student_id'] = user.id
                request.session['username'] = user.username
                
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid password')
        except StudentAccount.DoesNotExist:
            messages.error(request, 'User does not exist')
    return render(request, 'login.html')

def logout(request):
    request.session.flush()
    return redirect('login') 