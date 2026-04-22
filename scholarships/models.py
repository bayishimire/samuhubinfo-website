from django.db import models
from django.conf import settings  # Use AUTH_USER_MODEL
from django.utils import timezone


# Scholarship Model
# -------------------------------
class Scholarship(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('UPCOMING', 'Upcoming'),
        ('ENDED', 'Ended'),
        ('EXTENDED', 'Extended'),
    ]

    DEGREE_CHOICES = [
        ('ORGANIZATION_CERTIFICATE', 'Organization Certificate (OGC)'),
        ('ADVANCED_DIPLOMA', 'Advanced Diploma (A2)'),
        ('BACHELOR_DEGREE', 'Bachelor Degree (A0 / BSc)'),
        ('MASTERS_DEGREE', 'Masters Degree (MSc)'),
        ('PHD_DEGREE', 'PhD Degree (PhD)'),
        ('NO_DEGREE', 'No Degree'),
    ]

    title = models.CharField(max_length=200)
    university = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    degree_level = models.CharField(max_length=50, choices=DEGREE_CHOICES)
    description = models.TextField()
    eligibility = models.TextField()
    image = models.ImageField(upload_to='scholarship_images/', blank=True, null=True)
    application_link = models.URLField()
    deadline = models.DateField()
    posted_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    is_active = models.BooleanField(default=True)
    is_open = models.BooleanField(default=False)  # True if users can apply

    def save(self, *args, **kwargs):
        today = timezone.now().date()

        if self.status == 'EXTENDED':
            pass  # Manually extended, keep status
        elif self.deadline < today:
            self.status = 'ENDED'
        elif self.posted_date.date() > today:
            self.status = 'UPCOMING'
        else:
            self.status = 'OPEN'

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


# -------------------------------
# Scholarship Application Model
# -------------------------------
class ScholarshipApplication(models.Model):
    MARITAL_STATUS_CHOICES = [
        ('SINGLE', 'Single'),
        ('MARRIED', 'Married'),
        ('OTHER', 'Other'),
    ]

    # Link to User & Scholarship
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    scholarship = models.ForeignKey(Scholarship, on_delete=models.CASCADE)

    # Personal Information
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    country = models.CharField(max_length=100)
    village = models.CharField(max_length=100, blank=True, null=True)
    cell = models.CharField(max_length=20)
    nationality = models.CharField(max_length=100)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES)

    # Education Information
    highest_qualification = models.TextField(max_length=200, blank=True, null=False)
    education_background = models.TextField(
        help_text="Describe your education background from top to higher level"
    )
    CV_file_upload = models.FileField(upload_to='cv/', blank=True, null=True)
    application_Lettle = models.FileField(upload_to='application_lettle/', blank=True, null=True)

    photo=models.ImageField(upload_to='application/photo',blank=False,null=False)
    # Guardian Information
    guardian_name = models.CharField(max_length=200)
    guardian_address = models.CharField(max_length=900)
    guardian_location = models.CharField(max_length=200)
    guardian_phone = models.CharField(max_length=20)
    guardian_email = models.EmailField(unique=True)

    # Documents
    passport = models.FileField(upload_to='documents/', blank=True, null=True)
    visa = models.FileField(upload_to='documents/', blank=True, null=True)
    bank_statement = models.FileField(upload_to='documents/', blank=True, null=True)
    other_documents = models.FileField(upload_to='documents/', blank=True, null=True)

    # Application Status
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)

    applied_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.scholarship.title}"
