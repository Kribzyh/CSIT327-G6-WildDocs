from django.contrib import admin
from .models import StudentAccount

@admin.register(StudentAccount)
class StudentAccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'student_id', 'course', 'year_level')
    search_fields = ('username', 'email', 'student_id')
