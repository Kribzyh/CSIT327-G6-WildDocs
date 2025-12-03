"""
Utility functions for request management and processing.
"""

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import Request, StudentAccount, Notification, RequestWorkflow
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def send_status_notification(request_obj, old_status, new_status):
    """Send notification when request status changes"""
    try:
        # Create database notification - short format for display
        message = f"Request #{request_obj.id}: Status updated"
        
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
        'pending_requests': requests.filter(status__in=RequestWorkflow.pending_statuses()).count(),
        'approved_requests': requests.filter(status__in=RequestWorkflow.approval_statuses()).count(),
        'completed_requests': requests.filter(status__in=RequestWorkflow.completed_statuses()).count(),
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
    completed_requests = requests.filter(status__in=RequestWorkflow.completed_statuses())
    if completed_requests:
        total_days = sum((timezone.now() - req.date_requested).days for req in completed_requests)
        summary['average_processing_time'] = total_days / completed_requests.count()
    
    return summary


def check_overdue_requests():
    """Check for overdue approved requests and send reminders"""
    threshold_date = timezone.now() - timedelta(days=14)  # 14 days threshold
    overdue_requests = Request.objects.filter(
        status__in={
            RequestWorkflow.APPROVED_FOR_PAYMENT,
            RequestWorkflow.READY_FOR_PICKUP,
            RequestWorkflow.LEGACY_APPROVED
        },
        date_requested__lt=threshold_date
    )
    
    reminder_count = 0
    for request_obj in overdue_requests:
        try:
            # Send reminder notification - short format
            message = f"Request #{request_obj.id}: Ready for pickup - please claim soon"
            
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

    if request_obj.requirements_instructions:
        timeline.append({
            'date': None,
            'title': 'Requirements Posted',
            'description': request_obj.requirements_instructions,
            'status': 'current' if request_obj.status in RequestWorkflow.requirements_upload_statuses() else 'completed',
            'icon': 'fas fa-list-check'
        })

    if request_obj.requirements_submitted_at:
        timeline.append({
            'date': request_obj.requirements_submitted_at,
            'title': 'Requirements Submitted',
            'description': request_obj.requirements_submission_note or 'Files uploaded by student',
            'status': 'completed' if request_obj.requirements_verified_at else 'current',
            'icon': 'fas fa-upload'
        })

    if request_obj.requirements_verified_at:
        timeline.append({
            'date': request_obj.requirements_verified_at,
            'title': 'Requirements Verified',
            'description': request_obj.requirements_feedback or 'Registrar verified the uploaded requirements.',
            'status': 'completed',
            'icon': 'fas fa-clipboard-check'
        })

    if request_obj.payment_submitted_at:
        timeline.append({
            'date': request_obj.payment_submitted_at,
            'title': 'Payment Submitted',
            'description': request_obj.payment_reference_code or 'Receipt uploaded by student.',
            'status': 'completed' if request_obj.payment_verified_at else 'current',
            'icon': 'fas fa-receipt'
        })

    if request_obj.payment_verified_at:
        timeline.append({
            'date': request_obj.payment_verified_at,
            'title': 'Payment Verified',
            'description': request_obj.payment_feedback or 'Registrar validated the payment.',
            'status': 'completed',
            'icon': 'fas fa-badge-check'
        })

    if request_obj.ready_for_pickup_at:
        timeline.append({
            'date': request_obj.ready_for_pickup_at,
            'title': 'Ready for Pickup',
            'description': 'Document prepared and awaiting collection.',
            'status': 'current' if request_obj.status != RequestWorkflow.COMPLETED else 'completed',
            'icon': 'fas fa-box-archive'
        })

    if request_obj.completed_at:
        timeline.append({
            'date': request_obj.completed_at,
            'title': 'Completed',
            'description': 'Document claimed by student.',
            'status': 'completed',
            'icon': 'fas fa-handshake'
        })
    elif request_obj.status in RequestWorkflow.approval_statuses():
        timeline.append({
            'date': None,
            'title': 'Processing',
            'description': 'Registrar is preparing your document.',
            'status': 'current',
            'icon': 'fas fa-spinner'
        })
    
    return timeline