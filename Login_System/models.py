from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Remove 'name' and 'password' — use username & AbstractUser.password
    email = models.EmailField(max_length=50, unique=True)
    image = models.ImageField(upload_to='profile_pics', default='default.jpg')
    sex = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    year = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    qualification = models.CharField(max_length=50, blank=True, null=True)
    experience = models.CharField(max_length=50, blank=True, null=True)

    User_type = (
        ('Admin', 'Admin'),
        ('User', 'User'),
        ('Student', 'Student'),
    )
    user_type = models.CharField(max_length=50, choices=User_type, default='User')
    is_approved = models.BooleanField(default=False)
    is_disabled = models.BooleanField(default=False)
    first_login = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Return a string instead of printing
        return f"{self.username} ({self.user_type}) - {self.email}"
    
    #add here model of chat box


class OTP(models.Model):
    """One-time codes for verifying email/first-login.

    Stores a short numeric code and a UUID token that can be used as a link.
    """
    import uuid
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=10)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    purpose = models.CharField(max_length=30, default='verification')

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() >= self.expires_at

    def mark_used(self):
        self.used = True
        self.save()
