from django.db import models
from django.conf import settings
from django.utils import timezone

# --------------------------
# Job model: Represents a job posting
# --------------------------
class Job(models.Model):
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=150)
    location = models.CharField(max_length=150)
    description = models.TextField()
    requirements = models.TextField()
    posted_at = models.DateTimeField(default=timezone.now)
    deadline = models.DateTimeField(null=True, blank=True)
    # in Job model
    require_cover_letter = models.BooleanField(default=False)
    require_resume = models.BooleanField(default=True)

    image = models.ImageField(upload_to='job_images/', blank=True, null=True)

    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posted_jobs'
    )
    # Optional single support document (PDF, ZIP, etc.)
    support_document = models.FileField(upload_to='job_docs/', blank=True, null=True)
    
    # New field: Experience required or not
    EXPERIENCE_CHOICES = [
        ('YES', 'Experience Required'),
        ('NO', 'No Experience Required'),
    ]
    experience_required = models.CharField(max_length=3, choices=EXPERIENCE_CHOICES, default='NO')

    # Job Mode (Remote/On-site/Hybrid)
    MODE_CHOICES = [
        ('REMOTE', 'Remote'),
        ('ONSITE', 'On-site'),
        ('HYBRID', 'Hybrid'),
    ]
    job_mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='ONSITE')

    # Detailed required documents
    required_documents_list = models.TextField(blank=True, help_text="List documents separated by commas")

    def __str__(self):
        return f"{self.title} at {self.company}"


# --------------------------
# JobDocument model: For multiple documents per job
# --------------------------
class JobDocument(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='job_docs/')

    def __str__(self):
        return f"{self.job.title} - {self.file.name}"


# --------------------------
# JobApplication model: Stores manual applications submitted by users
# --------------------------
class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications'
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    resume = models.FileField(upload_to='resumes/')
    cover_letter = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"{self.full_name} -> {self.job.title}"
