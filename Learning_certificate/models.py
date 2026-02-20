from django.db import models
from django.conf import settings  # for user model

User = settings.AUTH_USER_MODEL

# -------------------------------
# Course model
# -------------------------------
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # 0 = free
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        
        return f"{self.title} - ${self.price} (Created: {self.created_at.strftime('%Y-%m-%d')})"


# -------------------------------
# Enrollment model
# -------------------------------
class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'Student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    is_paid = models.BooleanField(default=False)
    is_approved_by_admin = models.BooleanField(default=False)
    enrollment_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')  # prevent duplicates

    def can_access(self):
        return self.is_paid or self.is_approved_by_admin


    def __str__(self):
        return f"{self.student.username} - {self.course.title}  enlolled on {self.enrollment_date}"

# -------------------------------
# Exam model
# -------------------------------
class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    total_marks = models.PositiveIntegerField(default=100)
    passing_marks = models.PositiveIntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.course.title} and {self.total_marks} marks)"

# -------------------------------
# Exam Result model
# -------------------------------
class ExamResult(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    marks_obtained = models.PositiveIntegerField()
    passed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.passed = self.marks_obtained >= self.exam.passing_marks
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.enrollment.student.username} - {self.exam.title} - {'Passed' if self.passed else 'Failed'}"

# -------------------------------
# Certificate model
# -------------------------------
class Certificate(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE)
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    is_issued = models.BooleanField(default=False)

    def can_issue(self):
        """
        Certificate can be issued only if all exams in the course are passed.
        """
        exams = Exam.objects.filter(course=self.enrollment.course)
        results = ExamResult.objects.filter(enrollment=self.enrollment, exam__in=exams)
        return exams.count() > 0 and all(result.passed for result in results)

    def issue_certificate(self):
        if self.can_issue():
            self.is_issued = True
            # Optionally, generate certificate PDF here
            self.save()

    def __str__(self):
        return f"Certificate - {self.enrollment.student.username} ({self.enrollment.course.title})"
