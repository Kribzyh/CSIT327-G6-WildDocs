from django.db import models
from django.utils import timezone
from accounts.models import Request, StudentAccount
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
        return Request.objects.filter(student=student, status='Pending').order_by('-date_requested')
    
    @staticmethod
    def get_approved_requests_for_student(student):
        """Get all approved requests for a student"""
        return Request.objects.filter(student=student, status='Approved').order_by('-date_requested')
    
    @staticmethod
    def get_completed_requests_for_student(student):
        """Get all completed requests for a student"""
        return Request.objects.filter(student=student, status='Completed').order_by('-date_requested')
    
    @staticmethod
    def get_request_statistics(student):
        """Get statistics for a student's requests"""
        total_requests = Request.objects.filter(student=student).count()
        pending_count = Request.objects.filter(student=student, status='Pending').count()
        approved_count = Request.objects.filter(student=student, status='Approved').count()
        completed_count = Request.objects.filter(student=student, status='Completed').count()
        
        return {
            'total': total_requests,
            'pending': pending_count,
            'approved': approved_count,
            'completed': completed_count,
        }
    
    @staticmethod
    def calculate_processing_time(request):
        """Calculate processing time for a request"""
        if request.status == 'Completed':
            # This would use actual completion date when that field exists
            return (timezone.now() - request.date_requested).days
        return None
    
    @staticmethod
    def get_overdue_approved_requests(days_threshold=30):
        """Get approved requests that are overdue for pickup"""
        threshold_date = timezone.now() - timedelta(days=days_threshold)
        return Request.objects.filter(
            status='Approved',
            date_requested__lt=threshold_date
        )
