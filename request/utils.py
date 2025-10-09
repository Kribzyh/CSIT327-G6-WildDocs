"""
Utility functions for request management and processing.
"""

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import Request, StudentAccount, Notification
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def send_status_notification(request_obj, old_status, new_status):
    """Send notification when request status changes"""
    try:
        # Create database notification
        message = f"Your request #{request_obj.id} for {request_obj.document.name} has been updated from {old_status} to {new_status}."
        
        if new_status == 'Approved':
            message += " Please visit the Registrar's Office to claim your document."
        elif new_status == 'Completed':
            message += " Thank you for using WildDocs!"
        
        Notification.objects.create(
            student=request_obj.student,
            request=request_obj,
            message=message
        )
        
        # Send email notification (if email settings are configured)
        if hasattr(settings, 'EMAIL_HOST') and request_obj.student.email:
            subject = f"WildDocs: Request #{request_obj.id} Status Update"
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [request_obj.student.email],
                fail_silently=True
            )
            
        logger.info(f"Notification sent for request #{request_obj.id} status change: {old_status} -> {new_status}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send notification for request #{request_obj.id}: {str(e)}")
        return False


def get_request_priority(request_obj):
    """Calculate priority score for a request based on various factors"""
    priority_score = 0
    
    # Age of request (older requests get higher priority)
    days_old = (timezone.now() - request_obj.date_requested).days
    priority_score += min(days_old * 2, 20)  # Max 20 points for age
    
    # Document type priority (some documents are more urgent)
    urgent_documents = ['Transcript of Records', 'Diploma', 'Certificate of Enrollment']
    if request_obj.document.name in urgent_documents:
        priority_score += 15
    
    # Number of copies (fewer copies = faster processing)
    if request_obj.copies <= 2:
        priority_score += 5
    
    return priority_score


def validate_request_data(request_data):
    """Validate request data before submission"""
    errors = []
    
    # Check required fields
    required_fields = ['document_type', 'purpose', 'copies']
    for field in required_fields:
        if not request_data.get(field):
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    # Validate copies count
    copies = request_data.get('copies', 0)
    try:
        copies = int(copies)
        if copies < 1 or copies > 10:
            errors.append("Number of copies must be between 1 and 10")
    except ValueError:
        errors.append("Invalid number of copies")
    
    # Validate purpose length
    purpose = request_data.get('purpose', '')
    if len(purpose.strip()) < 10:
        errors.append("Purpose must be at least 10 characters long")
    elif len(purpose) > 500:
        errors.append("Purpose must not exceed 500 characters")
    
    return errors


def generate_request_summary(student):
    """Generate a summary of requests for a student"""
    requests = Request.objects.filter(student=student)
    
    summary = {
        'total_requests': requests.count(),
        'pending_requests': requests.filter(status='Pending').count(),
        'approved_requests': requests.filter(status='Approved').count(),
        'completed_requests': requests.filter(status='Completed').count(),
        'recent_requests': requests.order_by('-date_requested')[:5],
        'most_requested_document': None,
        'average_processing_time': None
    }
    
    # Find most requested document
    document_counts = {}
    for req in requests:
        doc_name = req.document.name
        document_counts[doc_name] = document_counts.get(doc_name, 0) + 1
    
    if document_counts:
        summary['most_requested_document'] = max(document_counts, key=document_counts.get)
    
    # Calculate average processing time (this would be more accurate with completion dates)
    completed_requests = requests.filter(status='Completed')
    if completed_requests:
        total_days = sum((timezone.now() - req.date_requested).days for req in completed_requests)
        summary['average_processing_time'] = total_days / completed_requests.count()
    
    return summary


def check_overdue_requests():
    """Check for overdue approved requests and send reminders"""
    threshold_date = timezone.now() - timedelta(days=14)  # 14 days threshold
    overdue_requests = Request.objects.filter(
        status='Approved',
        date_requested__lt=threshold_date
    )
    
    reminder_count = 0
    for request_obj in overdue_requests:
        try:
            # Send reminder notification
            message = f"Reminder: Your approved request #{request_obj.id} for {request_obj.document.name} is ready for pickup at the Registrar's Office. Please claim it within 30 days of approval."
            
            Notification.objects.create(
                student=request_obj.student,
                request=request_obj,
                message=message
            )
            
            reminder_count += 1
            
        except Exception as e:
            logger.error(f"Failed to send reminder for request #{request_obj.id}: {str(e)}")
    
    logger.info(f"Sent {reminder_count} overdue request reminders")
    return reminder_count


def format_request_timeline(request_obj):
    """Format request timeline for display"""
    timeline = []
    
    # Request submitted
    timeline.append({
        'date': request_obj.date_requested,
        'title': 'Request Submitted',
        'description': f'Request for {request_obj.document.name} submitted',
        'status': 'completed',
        'icon': 'fas fa-paper-plane'
    })
    
    # Add status-specific events
    if request_obj.status in ['Approved', 'Completed']:
        timeline.append({
            'date': request_obj.date_requested,  # Would use actual approval date
            'title': 'Request Approved',
            'description': 'Request has been reviewed and approved for processing',
            'status': 'completed',
            'icon': 'fas fa-check-circle'
        })
    
    if request_obj.status == 'Completed':
        timeline.append({
            'date': request_obj.date_requested,  # Would use actual completion date
            'title': 'Document Ready',
            'description': 'Document has been processed and is ready for pickup',
            'status': 'completed',
            'icon': 'fas fa-file-check'
        })
        
        timeline.append({
            'date': request_obj.date_requested,  # Would use actual pickup date
            'title': 'Document Collected',
            'description': 'Document successfully collected from Registrar\'s Office',
            'status': 'completed',
            'icon': 'fas fa-hand-holding'
        })
    
    # Add pending/future events
    if request_obj.status == 'Pending':
        timeline.append({
            'date': None,
            'title': 'Under Review',
            'description': 'Request is being reviewed by administration',
            'status': 'pending',
            'icon': 'fas fa-hourglass-half'
        })
    
    if request_obj.status in ['Pending', 'Approved']:
        timeline.append({
            'date': None,
            'title': 'Ready for Pickup',
            'description': 'Document will be ready for collection',
            'status': 'pending' if request_obj.status == 'Pending' else 'current',
            'icon': 'fas fa-clipboard-check'
        })
    
    return timeline