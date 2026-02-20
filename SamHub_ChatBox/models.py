from django.conf import settings
from django.db import models
from django.utils import timezone

# ---------------- Messages Model ----------------
class Message(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='messages/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)
    deleted_by_user = models.BooleanField(default=False)
    deleted_by_admin = models.BooleanField(default=False)  # track admin deletion
    disappear_after = models.IntegerField(default=0)  # seconds, 0 = permanent
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies'
    )

    def has_disappeared(self):
        if self.disappear_after > 0:
            return (timezone.now() - self.created_at).total_seconds() > self.disappear_after
        return False

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"


# ---------------- Comment / Reply ----------------
class Comment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to='messages/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_by_admin = models.BooleanField(default=False)  # track admin deletion

    def __str__(self):
        return f"{self.user.username} reply: {self.content[:20]}"

# ---------------- AI Message Model ----------------
class AIMessage(models.Model):

    ROLE_CHOICES = (
        ("user", "User"),
        ("assistant", "Assistant"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )

    def __str__(self):
        return f"{self.role}: {self.content[:20]}"
