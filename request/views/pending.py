"""
Views for handling pending requests.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import StudentAccount, Request


@login_required
def requests_pending(request):
    """View for displaying pending requests"""
    try:
        student = StudentAccount.objects.get(user=request.user)
        pending_requests = Request.objects.filter(
            student=student, 
            status='Pending'
        ).order_by('-date_requested')
    except StudentAccount.DoesNotExist:
        pending_requests = []
    
    context = {
        'requests': pending_requests,
        'status': 'Pending',
        'page_title': 'Pending Requests',
        'total_count': len(pending_requests),
    }
    return render(request, 'Request/pending_requests.html', context)


@login_required
def cancel_pending_request(request, request_id):
    """View for cancelling a pending request"""
    try:
        student = StudentAccount.objects.get(user=request.user)
        req = Request.objects.get(id=request_id, student=student, status='Pending')
        
        if request.method == 'POST':
            # Update status to cancelled
            req.status = 'Cancelled'
            req.notes = f"Cancelled by student on {request.user.date_joined.strftime('%Y-%m-%d')}"
            req.save()
            
            # Redirect back to pending requests with success message
            return redirect('Request:pending')
    except (StudentAccount.DoesNotExist, Request.DoesNotExist):
        pass
    
    # If GET request or error, redirect to pending requests
    return redirect('Request:pending')