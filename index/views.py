from django.shortcuts import render, redirect

# Create your views here.
def home(request):
    # Prevent logged-in users from viewing the public homepage
    if request.user.is_authenticated:
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('dashboard')

    return render(request, 'home.html')