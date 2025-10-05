from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# --- Validator for standardized student IDs ---
id_validator = RegexValidator(
    regex=r'^\d{2}-\d{4}-\d{3}$',
    message="ID must be in the format YY-NNNN-NNN (e.g., 23-6385-642)."
)

# --- Student account linked to Django's User model ---
class StudentAccount(models.Model):
<<<<<<< HEAD
=======
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
>>>>>>> main
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[id_validator]
    )
    course = models.CharField(max_length=100, default="Undeclared")
    year_level = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} ({self.student_number})"


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
class Request(models.Model):
    student = models.ForeignKey(StudentAccount, on_delete=models.CASCADE)
    document = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    assigned_admin = models.ForeignKey(AdminAccount, on_delete=models.SET_NULL, null=True, blank=True)
    date_requested = models.DateTimeField(auto_now_add=True)
    purpose = models.TextField()
    copies = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=50, default='Pending')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Request #{self.id} by {self.student}"


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