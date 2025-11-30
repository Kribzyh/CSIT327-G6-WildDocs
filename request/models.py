from django.db import models
from django.utils import timezone
from accounts.models import Request, StudentAccount, RequestWorkflow
from datetime import datetime, timedelta


class RequestStatusHistory(models.Model):
    """Track status changes for requests"""
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=50, blank=True, null=True)
    new_status = models.CharField(max_length=50)
    changed_by = models.CharField(max_length=100)  # Could be 'System' or admin name
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name_plural = "Request Status Histories"
    
    def __str__(self):
        return f"Request #{self.request.id}: {self.old_status} → {self.new_status}"


class RequestComment(models.Model):
    """Comments and notes for requests"""
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='comments')
    author = models.CharField(max_length=100)  # Student or admin name
    comment = models.TextField()
    is_internal = models.BooleanField(default=False)  # Only visible to admins
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment on Request #{self.request.id} by {self.author}"


# Utility functions for request management
class RequestManager:
    """Utility class for managing requests"""
    
    @staticmethod
    def get_pending_requests_for_student(student):
        """Get all pending requests for a student"""
        return Request.objects.filter(
            student=student,
            status__in=RequestWorkflow.pending_statuses()
        ).order_by('-date_requested')
    
    @staticmethod
    def get_approved_requests_for_student(student):
        """Get all approved requests for a student"""
        return Request.objects.filter(
            student=student,
            status__in=RequestWorkflow.approval_statuses()
        ).order_by('-date_requested')
    
    @staticmethod
    def get_completed_requests_for_student(student):
        """Get all completed requests for a student"""
        return Request.objects.filter(
            student=student,
            status__in=RequestWorkflow.completed_statuses()
        ).order_by('-date_requested')
    
    @staticmethod
    def get_request_statistics(student):
        """Get statistics for a student's requests"""
        total_requests = Request.objects.filter(student=student).count()
        pending_count = Request.objects.filter(
            student=student,
            status__in=RequestWorkflow.pending_statuses()
        ).count()
        approved_count = Request.objects.filter(
            student=student,
            status__in=RequestWorkflow.approval_statuses()
        ).count()
        completed_count = Request.objects.filter(
            student=student,
            status__in=RequestWorkflow.completed_statuses()
        ).count()
        
        return {
            'total': total_requests,
            'pending': pending_count,
            'approved': approved_count,
            'completed': completed_count,
        }
    
    @staticmethod
    def calculate_processing_time(request):
        """Calculate processing time for a request"""
        if request.status in RequestWorkflow.completed_statuses():
            # This would use actual completion date when that field exists
            return (timezone.now() - request.date_requested).days
        return None
    
    @staticmethod
    def get_overdue_approved_requests(days_threshold=30):
        """Get approved requests that are overdue for pickup"""
        threshold_date = timezone.now() - timedelta(days=days_threshold)
        return Request.objects.filter(
            status__in=RequestWorkflow.approval_statuses(),
            date_requested__lt=threshold_date
        )


class RequirementUpload(models.Model):
    """Stores metadata for requirement files uploaded by students (backed by Supabase storage)."""
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='requirement_uploads')
    uploaded_by = models.ForeignKey(StudentAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploads')
    file_name = models.CharField(max_length=512)
    file_url = models.TextField(blank=True, null=True)
    supabase_id = models.CharField(max_length=255, blank=True, null=True)
    delete_url = models.TextField(blank=True, null=True)
    content_type = models.CharField(max_length=100, blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)
    provider = models.CharField(max_length=50, default='supabase')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Requirement Upload'
        verbose_name_plural = 'Requirement Uploads'

    def __str__(self):
        return f"Upload {self.file_name} for Request #{self.request.id}"


class PaymentUpload(models.Model):
    """Stores metadata for payment receipt files uploaded by students."""
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='payment_uploads')
    uploaded_by = models.ForeignKey(StudentAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_uploads')
    file_name = models.CharField(max_length=512)
    file_url = models.TextField(blank=True)
    supabase_id = models.CharField(max_length=255, blank=True, null=True)
    delete_url = models.TextField(blank=True)
    content_type = models.CharField(max_length=100, blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)
    provider = models.CharField(max_length=50, default='supabase')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment Upload'
        verbose_name_plural = 'Payment Uploads'

    def __str__(self):
        return f"Payment {self.file_name} for Request #{self.request.id}"
