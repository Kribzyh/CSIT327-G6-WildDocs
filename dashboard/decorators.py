from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied

def student_required(view_func):
    """
    Restrict access to student users only.
    Redirect admin/staff users away from student pages.
    """
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        # Block admin users
        if hasattr(user, 'adminaccount') or user.is_staff:
            messages.error(request, "Admins cannot access student dashboard pages.")
            return redirect('admin_dashboard')

        # Block users without a student account
        if not hasattr(user, 'studentaccount'):
            raise PermissionDenied("Student account required.")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
