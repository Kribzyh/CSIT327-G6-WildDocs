"""
Views for handling request details.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import StudentAccount, Request


@login_required
def request_detail(request, request_id):
    """View for displaying detailed information about a specific request"""
    try:
        student = StudentAccount.objects.get(user=request.user)
        req = Request.objects.get(id=request_id, student=student)
        
        # Add additional context based on request status
        context = {
            'request': req,
            'page_title': 'Request Details',
            'can_cancel': req.status == 'Pending',
            'can_download_receipt': req.status == 'Completed',
            'can_print_slip': req.status == 'Approved',
        }
        
        return render(request, 'Request/request_detail.html', context)
    except (StudentAccount.DoesNotExist, Request.DoesNotExist):
        req = None
        context = {
            'request': req,
            'page_title': 'Request Details'
        }
        return render(request, 'Request/request_detail.html', context)


@login_required
def request_timeline(request, request_id):
    """View for displaying the timeline/history of a specific request"""
    try:
        student = StudentAccount.objects.get(user=request.user)
        req = Request.objects.get(id=request_id, student=student)
        
        # Create timeline events (this would be enhanced with actual timeline data)
        timeline_events = [
            {
                'date': req.date_requested,
                'title': 'Request Submitted',
                'description': f'Request for {req.document.name} submitted',
                'status': 'completed'
            }
        ]
        
        # Add status-specific events
        if req.status in ['Approved', 'Completed']:
            timeline_events.append({
                'date': req.date_requested,  # This would be actual approval date
                'title': 'Request Approved',
                'description': 'Your request has been approved and is ready for pickup',
                'status': 'completed'
            })
        
        if req.status == 'Completed':
            timeline_events.append({
                'date': req.date_requested,  # This would be actual completion date
                'title': 'Document Collected',
                'description': 'Document successfully collected from Registrar\'s Office',
                'status': 'completed'
            })
        
        context = {
            'request': req,
            'timeline_events': timeline_events,
            'page_title': f'Request #{req.id} Timeline'
        }
        
        return render(request, 'Request/request_timeline.html', context)
    except (StudentAccount.DoesNotExist, Request.DoesNotExist):
        return redirect('Request:detail', request_id=request_id)