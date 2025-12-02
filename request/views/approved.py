"""
Views for handling approved requests (Ready for Pick Up).
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from accounts.models import StudentAccount, Request, RequestWorkflow
import datetime


@login_required
def requests_approved(request):
    """View for displaying requests that are ready for pickup"""
    try:
        student = StudentAccount.objects.get(user=request.user)
        # Only show requests marked as "Ready for Pickup" by staff
        approved_requests = Request.objects.filter(
            student=student, 
            status=RequestWorkflow.READY_FOR_PICKUP
        ).order_by('-date_requested')
    except StudentAccount.DoesNotExist:
        approved_requests = []
    
    context = {
        'requests': approved_requests,
        'status': 'Ready for Pick Up',
        'page_title': 'Ready for Pick Up',
        'total_count': len(approved_requests),
    }
    return render(request, 'Request/approved_requests.html', context)


@login_required
def generate_pickup_slip(request, request_id):
    """View for generating a pickup slip for a request ready for pickup"""
    try:
        student = StudentAccount.objects.get(user=request.user)
        req = Request.objects.get(
            id=request_id, 
            student=student, 
            status=RequestWorkflow.READY_FOR_PICKUP
        )
        
        # Generate pickup slip content
        context = {
            'request': req,
            'student': student,
            'generated_date': datetime.datetime.now(),
        }
        
        return render(request, 'Request/pickup_slip.html', context)
    except (StudentAccount.DoesNotExist, Request.DoesNotExist):
        return redirect('Request:approved')