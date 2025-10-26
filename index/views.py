from django.shortcuts import render, redirect

def home(request):
    # ✅ If the user is logged in, redirect based on role
    if request.user.is_authenticated:
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)

        # Role-based redirection
        if hasattr(request.user, 'adminaccount'):
            return redirect('admin_dashboard')  # Staff → Admin dashboard
        elif hasattr(request.user, 'studentaccount'):
            return redirect('dashboard')        # Student → Student dashboard
        else:
            return redirect('dashboard')        # Default fallback

    # If not logged in → show public homepage
    return render(request, 'home.html')
