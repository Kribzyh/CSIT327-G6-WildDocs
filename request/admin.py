from django.contrib import admin
from .models import RequestStatusHistory, RequestComment

# Register your models here.

@admin.register(RequestStatusHistory)
class RequestStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['request', 'old_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['new_status', 'changed_at', 'changed_by']
    search_fields = ['request__id', 'request__student__user__username']
    readonly_fields = ['changed_at']
    ordering = ['-changed_at']

@admin.register(RequestComment)
class RequestCommentAdmin(admin.ModelAdmin):
    list_display = ['request', 'author', 'comment_preview', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['request__id', 'author', 'comment']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def comment_preview(self, obj):
        """Return a preview of the comment"""
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment Preview'
