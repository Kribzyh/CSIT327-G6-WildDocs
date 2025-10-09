"""
Views for handling completed requests.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from accounts.models import StudentAccount, Request
import datetime


@login_required
def requests_completed(request):
    """View for displaying completed requests"""
    try:
        student = StudentAccount.objects.get(user=request.user)
        completed_requests = Request.objects.filter(
            student=student, 
            status='Completed'
        ).order_by('-date_requested')
    except StudentAccount.DoesNotExist:
        completed_requests = []
    
    context = {
        'requests': completed_requests,
        'status': 'Completed',
        'page_title': 'Completed Requests',
        'total_count': len(completed_requests),
    }
    return render(request, 'Request/completed_requests.html', context)


@login_required
def download_completion_receipt(request, request_id):
    """View for downloading a completion receipt for a completed request"""
    try:
        student = StudentAccount.objects.get(user=request.user)
        req = Request.objects.get(id=request_id, student=student, status='Completed')
        
        # Generate receipt content
        context = {
            'request': req,
            'student': student,
            'completion_date': datetime.datetime.now(),
        }
        
        return render(request, 'Request/completion_receipt.html', context)
    except (StudentAccount.DoesNotExist, Request.DoesNotExist):
        return redirect('Request:completed')


@login_required
def request_statistics(request):
    """View for displaying request statistics for completed requests"""
    try:
        student = StudentAccount.objects.get(user=request.user)
        completed_requests = Request.objects.filter(
            student=student, 
            status='Completed'
        )
        
        # Calculate statistics
        total_completed = completed_requests.count()
        document_types = {}
        for req in completed_requests:
            doc_type = req.document.name
            if doc_type in document_types:
                document_types[doc_type] += 1
            else:
                document_types[doc_type] = 1
        
        context = {
            'total_completed': total_completed,
            'document_types': document_types,
            'recent_requests': completed_requests[:5],
        }
        
        return render(request, 'Request/request_statistics.html', context)
    except StudentAccount.DoesNotExist:
        return redirect('Request:completed')