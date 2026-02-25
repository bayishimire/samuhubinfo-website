from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification, User
from Learning_certificate.models import Course
from Job_Opportunity.models import Job
from scholarships.models import Scholarship

def create_notifications_for_all_users(title, message, category, link=None):
    users = User.objects.filter(is_active=True)
    notifications = [
        Notification(
            user=user,
            title=title,
            message=message,
            category=category,
            link=link
        ) for user in users
    ]
    Notification.objects.bulk_create(notifications)

    # Send email to all users (simplistic approach for now)
    user_emails = users.values_list('email', flat=True)
    if user_emails:
        try:
            send_mail(
                subject=title,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(user_emails),
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error sending bulk email: {e}")

@receiver(post_save, sender=Course)
def course_notification(sender, instance, created, **kwargs):
    if created:
        title = f"New Course: {instance.title}"
        message = f"Check out our new course: {instance.title}. {instance.description[:100]}..."
        link = f"/Learning_certificate/courses/{instance.id}/"
        create_notifications_for_all_users(title, message, 'COURSE', link)

@receiver(post_save, sender=Job)
def job_notification(sender, instance, created, **kwargs):
    if created:
        title = f"New Job Opening: {instance.title}"
        message = f"A new job has been posted: {instance.title} at {instance.company}."
        link = f"/Job_Opportunity/jobs/" # Assuming a list view for now
        create_notifications_for_all_users(title, message, 'JOB', link)

@receiver(post_save, sender=Scholarship)
def scholarship_notification(sender, instance, created, **kwargs):
    if created:
        title = f"New Scholarship: {instance.title}"
        message = f"A new scholarship opportunity is available: {instance.title} at {instance.university}."
        link = f"/scholarships/" # Assuming a list view
        create_notifications_for_all_users(title, message, 'ADV', link)
