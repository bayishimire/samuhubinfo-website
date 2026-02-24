from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL


# ═══════════════════════════════════════════════
# 1. COURSE — created by super/admin
# ═══════════════════════════════════════════════
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    # Rich content the enrolled student will study
    content = models.TextField(
        blank=True, null=True,
        help_text="Full course material (HTML allowed). Only enrolled students can see this."
    )
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # 0 = free

    # Duration & scheduling
    duration_weeks = models.PositiveIntegerField(
        default=4,
        help_text="How many weeks the course runs."
    )
    start_date = models.DateTimeField(
        blank=True, null=True,
        help_text="When the course opens for learning."
    )
    end_date = models.DateTimeField(
        blank=True, null=True,
        help_text="When the course closes."
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def is_open_for_learning(self):
        """Course content is accessible only between start and end dates."""
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    def __str__(self):
        return f"{self.title} ({self.duration_weeks}w)"


# ═══════════════════════════════════════════════
# 2. ENROLLMENT — student signs up for a course
# ═══════════════════════════════════════════════
class Enrollment(models.Model):
    student = models.ForeignKey(
        User, on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'Student'}
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    is_paid = models.BooleanField(default=False)
    is_approved_by_admin = models.BooleanField(default=False)
    enrollment_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def can_access(self):
        """Student can access course content if paid/approved."""
        return self.is_paid or self.is_approved_by_admin

    def __str__(self):
        return f"{self.student} → {self.course.title}"


# ═══════════════════════════════════════════════
# 3. EXAM — created by super admin, scheduled
# ═══════════════════════════════════════════════
class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    total_marks = models.PositiveIntegerField(default=100)
    passing_marks = models.PositiveIntegerField(default=50)

    # Scheduling — super admin sets when exam opens/closes
    open_date = models.DateTimeField(
        blank=True, null=True,
        help_text="When the exam becomes available to students."
    )
    close_date = models.DateTimeField(
        blank=True, null=True,
        help_text="Deadline — exam closes after this."
    )
    duration_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Time limit in minutes once the student starts."
    )

    is_published = models.BooleanField(
        default=False,
        help_text="Only published exams are visible to students."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['open_date']

    def is_open(self):
        """Exam is open between open_date and close_date."""
        if not self.open_date or not self.close_date:
            return False
        now = timezone.now()
        return self.is_published and self.open_date <= now <= self.close_date

    def status_label(self):
        now = timezone.now()
        if not self.is_published:
            return 'draft'
        if not self.open_date or not self.close_date:
            return 'draft'
        if now < self.open_date:
            return 'upcoming'
        if self.open_date <= now <= self.close_date:
            return 'open'
        return 'closed'

    def __str__(self):
        return f"{self.title} — {self.course.title}"


# ═══════════════════════════════════════════════
# 4. QUESTION — multiple-choice questions
# ═══════════════════════════════════════════════
class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(help_text="The question text.")
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)

    ANSWER_CHOICES = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ]
    correct_answer = models.CharField(max_length=1, choices=ANSWER_CHOICES)
    marks = models.PositiveIntegerField(default=1, help_text="Points for this question.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Q{self.order}: {self.text[:60]}"

    def get_options(self):
        """Return list of (letter, text) tuples for template iteration."""
        return [
            ('A', self.option_a),
            ('B', self.option_b),
            ('C', self.option_c),
            ('D', self.option_d),
        ]


# ═══════════════════════════════════════════════
# 5. EXAM ATTEMPT — student starts an exam
# ═══════════════════════════════════════════════
class ExamAttempt(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='attempts')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    is_submitted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('enrollment', 'exam')  # one attempt per exam

    def time_remaining(self):
        """Seconds remaining before time expires."""
        if self.is_submitted:
            return 0
        deadline = self.started_at + timezone.timedelta(minutes=self.exam.duration_minutes)
        remaining = (deadline - timezone.now()).total_seconds()
        return max(0, remaining)

    def is_expired(self):
        return self.time_remaining() <= 0

    def __str__(self):
        return f"{self.enrollment.student} — {self.exam.title}"


# ═══════════════════════════════════════════════
# 6. STUDENT ANSWER — one per question per attempt
# ═══════════════════════════════════════════════
class StudentAnswer(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=1, choices=Question.ANSWER_CHOICES, blank=True)

    class Meta:
        unique_together = ('attempt', 'question')

    def is_correct(self):
        return self.selected_answer == self.question.correct_answer

    def __str__(self):
        return f"Q{self.question.order} → {self.selected_answer}"


# ═══════════════════════════════════════════════
# 7. EXAM RESULT — auto-generated after submission
# ═══════════════════════════════════════════════
class ExamResult(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='results')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    attempt = models.OneToOneField(ExamAttempt, on_delete=models.CASCADE, related_name='result')
    marks_obtained = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    # Track notifications
    certificate_sent = models.BooleanField(default=False)
    retake_notified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.passed = self.marks_obtained >= self.exam.passing_marks
        super().save(*args, **kwargs)

    def percentage(self):
        if self.total_marks == 0:
            return 0
        return round((self.marks_obtained / self.total_marks) * 100, 1)

    def __str__(self):
        status = 'PASSED ✓' if self.passed else 'FAILED ✗'
        return f"{self.enrollment.student} — {self.exam.title} — {status} ({self.marks_obtained}/{self.total_marks})"


# ═══════════════════════════════════════════════
# 8. CERTIFICATE — issued when all exams passed
# ═══════════════════════════════════════════════
class Certificate(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate')
    certificate_number = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    is_issued = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)

    def can_issue(self):
        """All exams for the course must be passed."""
        exams = self.enrollment.course.exams.filter(is_published=True)
        if exams.count() == 0:
            return False

        for exam in exams:
            result = ExamResult.objects.filter(
                enrollment=self.enrollment,
                exam=exam,
                passed=True
            ).first()
            if not result:
                return False

        # Max 50 certificates per course
        issued_count = Certificate.objects.filter(
            enrollment__course=self.enrollment.course,
            is_issued=True
        ).count()
        return issued_count < 50

    def issue_certificate(self):
        if self.can_issue():
            self.is_issued = True
            self.save()
            return True
        return False

    def __str__(self):
        return f"Certificate — {self.enrollment.student} ({self.enrollment.course.title})"
