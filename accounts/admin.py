from django.contrib import admin
from .models import StudentAccount, Staff

@admin.register(StudentAccount)
class StudentAccountAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'student_id', 'course', 'year_level')
    search_fields = ('full_name', 'email', 'student_id')

    def full_name(self, obj):
        return f"{obj.last_name}, {obj.first_name}"

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_email', 'staff_id', 'department')
    search_fields = ('user__username', 'user__email', 'staff_id', 'department')

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'