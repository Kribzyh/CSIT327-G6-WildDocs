# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password, check_password

student_id_validator = RegexValidator(
    regex=r'^\d{2}-\d{4}-\d{3}$',
    message="Student ID must be in the format YY-NNNN-NNN (e.g., 23-6385-642)."
)

class StudentAccount(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # hashed password
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    student_id = models.CharField(
        max_length=20,
        unique=True,
        validators=[student_id_validator]
    )
    course = models.CharField(max_length=100, blank=True, null=True)
    year_level = models.IntegerField(blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)

    def save(self, *args, **kwargs):
        # hash the password if it’s not already hashed
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.username} ({self.student_id})"
    

class Staff(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length = 100)
    department = models.CharField(max_length=100, blank=True, null=True)
        
    def __str__(self):

        return f"{self.user.username} ({self.role})"
    
    