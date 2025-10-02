from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password, check_password

id_validator = RegexValidator(
    regex=r'^\d{2}-\d{4}-\d{3}$',
    message="ID must be in the format YY-NNNN-NNN (e.g., 23-6385-642)."
)

class StudentAccount(models.Model):
    student_id = models.CharField(
        max_length=20,
        unique=True,
        validators=[id_validator]
    )
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # hashed password
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    course = models.CharField(max_length=100, blank=True, null=True)
    program = models.CharField(max_length=50, blank=True, null=True)  # Add this field
    year_level = models.IntegerField(blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)  # Add this line

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.student_id})"


class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=100)
    staff_id = models.CharField(
        max_length=20,
        unique=True,
        validators=[id_validator]
    )
    department = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"