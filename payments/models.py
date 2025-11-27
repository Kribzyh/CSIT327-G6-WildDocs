
from django.db import models
from accounts.models import Request
# Register your models here.


class Payment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    # Link to the student account (optional)
    user = models.ForeignKey('accounts.StudentAccount', on_delete=models.SET_NULL, null=True, blank=True)
    # Optionally link to a request (if payment is for a document request)
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='payments_payments')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='PHP')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # Unique reference from the payment provider / client
    reference = models.CharField(max_length=128, unique=True)

    # ID of the row in Supabase (if synced)
    supabase_id = models.CharField(max_length=255, null=True, blank=True)

    # JSON payload returned or associated metadata
    metadata = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference} - {self.amount} {self.currency}"


