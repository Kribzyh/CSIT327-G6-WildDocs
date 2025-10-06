from django.contrib import admin
from .models import StudentAccount, AdminAccount


@admin.register(StudentAccount)
class StudentAccountAdmin(admin.ModelAdmin):
    list_display = (
        'get_username',
        'get_first_name',
        'get_last_name',
        'get_email',
        'student_number',
        'course',
        'year_level',
    )
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'student_number',
    )

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    def get_first_name(self, obj):
        return obj.user.first_name
    get_first_name.short_description = 'First Name'

    def get_last_name(self, obj):
        return obj.user.last_name
    get_last_name.short_description = 'Last Name'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'


@admin.register(AdminAccount)
class AdminAccountAdmin(admin.ModelAdmin):
    list_display = (
        'get_username',
        'get_first_name',
        'get_last_name',
        'get_email',
        'full_name',
        'role',
        'is_active',
    )
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'full_name',
        'role',
    )

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    def get_first_name(self, obj):
        return obj.user.first_name
    get_first_name.short_description = 'First Name'

    def get_last_name(self, obj):
        return obj.user.last_name
    get_last_name.short_description = 'Last Name'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'