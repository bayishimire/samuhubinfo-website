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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Return a string instead of printing
        return f"{self.username} ({self.user_type}) - {self.email}"
    
    #add here model of chat box
