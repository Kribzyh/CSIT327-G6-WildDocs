from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.files.storage import default_storage
from django.utils import timezone
import uuid
import os

# --- Validator for standardized student IDs ---
id_validator = RegexValidator(
    regex=r'^\d{2}-\d{4}-\d{3}$',
    message="ID must be in the format YY-NNNN-NNN (e.g., 23-6385-642)."
)

def upload_to_supabase(instance, filename):
    """Upload profile pictures to Supabase Storage"""
    # Generate unique filename to avoid conflicts
    file_extension = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    return f'profile_pictures/{instance.student_number}/{unique_filename}'

# --- Student account linked to Django's User model ---
class StudentAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[id_validator]
    )
    first_name = models.CharField(max_length=50, default="")
    last_name = models.CharField(max_length=50, default="")
    email = models.EmailField(max_length=100, default="")
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.URLField(max_length=500, blank=True, null=True)  # Store Supabase URL
    course = models.CharField(max_length=100, default="Undeclared")
    program = models.CharField(max_length=100, default="Other")
    year_level = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.user.first_name} {self.last_name}"


# --- Admin account (school staff) ---
class AdminAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.full_name


# --- Different types of requestable documents ---
class DocumentType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    requirements = models.TextField(blank=True, null=True)
    fee = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name


# --- Request made by a student for a document ---
class RequestWorkflow:
    """Status helper for the document request workflow."""

    # Primary workflow states (human-friendly values stored in DB)
    PENDING_REVIEW = "Pending (For Review)"
    REQUIREMENTS_NEEDED = "Requirements Needed"
    REQUIREMENTS_SUBMITTED = "Requirements Submitted – For Verification"
    REQUIREMENTS_ISSUE = "Requirements Issue"
    APPROVED_FOR_PAYMENT = "Requirements Approved – For Payment"
    PAYMENT_SUBMITTED = "Payment Submitted – For Verification"
    PAYMENT_ISSUE = "Payment Issue"
    PROCESSING = "Processing"
    READY_FOR_PICKUP = "Ready for Pickup"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"

    # Legacy states kept for backward compatibility with historical data/UI
    LEGACY_PENDING = "Pending"
    LEGACY_APPROVED = "Approved"
    LEGACY_COMPLETED = "Completed"

    @classmethod
    def pending_statuses(cls):
        return {
            cls.PENDING_REVIEW,
            cls.REQUIREMENTS_NEEDED,
            cls.REQUIREMENTS_SUBMITTED,
            cls.REQUIREMENTS_ISSUE,
            cls.LEGACY_PENDING,
        }

    @classmethod
    def approval_statuses(cls):
        return {
            cls.APPROVED_FOR_PAYMENT,
            cls.PAYMENT_SUBMITTED,
            cls.PAYMENT_ISSUE,
            cls.PROCESSING,
            cls.READY_FOR_PICKUP,
            cls.LEGACY_APPROVED,
        }

    @classmethod
    def completed_statuses(cls):
        return {cls.COMPLETED, cls.LEGACY_COMPLETED}

    @classmethod
    def requirements_upload_statuses(cls):
        return {cls.REQUIREMENTS_NEEDED, cls.REQUIREMENTS_ISSUE}

    @classmethod
    def payment_upload_statuses(cls):
        return {cls.APPROVED_FOR_PAYMENT, cls.PAYMENT_ISSUE}

    @classmethod
    def status_label(cls, value):
        """Return a safe display label even for legacy values."""
        display_map = {
            cls.PENDING_REVIEW: cls.PENDING_REVIEW,
            cls.REQUIREMENTS_NEEDED: cls.REQUIREMENTS_NEEDED,
            cls.REQUIREMENTS_SUBMITTED: cls.REQUIREMENTS_SUBMITTED,
            cls.REQUIREMENTS_ISSUE: cls.REQUIREMENTS_ISSUE,
            cls.APPROVED_FOR_PAYMENT: cls.APPROVED_FOR_PAYMENT,
            cls.PAYMENT_SUBMITTED: cls.PAYMENT_SUBMITTED,
            cls.PAYMENT_ISSUE: cls.PAYMENT_ISSUE,
            cls.PROCESSING: cls.PROCESSING,
            cls.READY_FOR_PICKUP: cls.READY_FOR_PICKUP,
            cls.COMPLETED: cls.COMPLETED,
            cls.CANCELLED: cls.CANCELLED,
            cls.REJECTED: cls.REJECTED,
            cls.LEGACY_PENDING: cls.PENDING_REVIEW,
            cls.LEGACY_APPROVED: cls.APPROVED_FOR_PAYMENT,
            cls.LEGACY_COMPLETED: cls.COMPLETED,
        }
        return display_map.get(value, value)


class Request(models.Model):
    student = models.ForeignKey(StudentAccount, on_delete=models.CASCADE)
    document = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    assigned_admin = models.ForeignKey(AdminAccount, on_delete=models.SET_NULL, null=True, blank=True)
    date_requested = models.DateTimeField(auto_now_add=True)
    purpose = models.TextField()
    copies = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=50, default='Pending')
    notes = models.TextField(blank=True, null=True)
    requirements_instructions = models.TextField(blank=True, null=True)
    requirements_submission_note = models.TextField(blank=True, null=True)
    requirements_submission_file = models.FileField(upload_to='requirements_submissions/', blank=True, null=True)
    requirements_submitted_at = models.DateTimeField(blank=True, null=True)
    requirements_verified_at = models.DateTimeField(blank=True, null=True)
    requirements_feedback = models.TextField(blank=True, null=True)
    payment_reference_code = models.CharField(max_length=100, blank=True, null=True)
    # Store primary payment receipt as a public URL (Supabase) for backward compatibility
    payment_receipt = models.URLField(max_length=500, blank=True, null=True)
    payment_submitted_at = models.DateTimeField(blank=True, null=True)
    payment_verified_at = models.DateTimeField(blank=True, null=True)
    payment_feedback = models.TextField(blank=True, null=True)
    ready_for_pickup_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Request #{self.id} by {self.student}"

    # Convenience helpers -------------------------------------------------
    def status_label(self):
        return RequestWorkflow.status_label(self.status)

    def requires_requirements_upload(self):
        return self.status in RequestWorkflow.requirements_upload_statuses()

    def requires_payment_upload(self):
        return self.status in RequestWorkflow.payment_upload_statuses()

    def mark_completed(self):
        self.status = RequestWorkflow.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])

    def workflow_stage(self):
        if self.status in RequestWorkflow.pending_statuses():
            return 'pending'
        if self.status in RequestWorkflow.completed_statuses():
            return 'completed'
        if self.status in RequestWorkflow.requirements_upload_statuses():
            return 'requirements'
        if self.status in RequestWorkflow.payment_upload_statuses():
            return 'payment'
        if self.status in {RequestWorkflow.REQUIREMENTS_ISSUE, RequestWorkflow.PAYMENT_ISSUE}:
            return 'issue'
        if self.status in {
            RequestWorkflow.PAYMENT_SUBMITTED,
            RequestWorkflow.PROCESSING,
            RequestWorkflow.READY_FOR_PICKUP,
            RequestWorkflow.APPROVED_FOR_PAYMENT,
        }:
            return 'in-progress'
        return 'pending'


# --- Payment associated with a request ---
class Payment(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_status = models.CharField(max_length=50, default="Unpaid")
    date_paid = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Payment for {self.request}"


# --- Attachments uploaded for a request ---
class Attachment(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/')
    file_size = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Attachment {self.id} for Request {self.request.id}"


# --- Notifications sent to students ---
class Notification(models.Model):
    student = models.ForeignKey(StudentAccount, on_delete=models.CASCADE)
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    message = models.TextField()
    date_sent = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.student}"