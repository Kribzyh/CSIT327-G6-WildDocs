from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = ('reference', 'user', 'request', 'amount', 'currency', 'status', 'supabase_id', 'created_at')
	search_fields = ('reference', 'supabase_id', 'user__student_number', 'user__email')
	list_filter = ('status', 'currency', 'created_at')
