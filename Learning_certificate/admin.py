from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import (
    Course, Enrollment, Exam, Question,
    ExamAttempt, StudentAnswer, ExamResult, Certificate
)

User = get_user_model()


# ═══════════════════════════════════════════════
# Inline: Questions inside Exam
# ═══════════════════════════════════════════════
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('order', 'text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'marks')


# ═══════════════════════════════════════════════
# Inline: Exams inside Course
# ═══════════════════════════════════════════════
class ExamInline(admin.TabularInline):
    model = Exam
    extra = 0
    fields = ('title', 'total_marks', 'passing_marks', 'open_date', 'close_date', 'duration_minutes', 'is_published')
    show_change_link = True


# ═══════════════════════════════════════════════
# Course Admin
# ═══════════════════════════════════════════════
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'duration_weeks', 'start_date', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    inlines = [ExamInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'thumbnail', 'price')
        }),
        ('Schedule & Duration', {
            'fields': ('duration_weeks', 'start_date', 'end_date', 'is_active'),
            'description': 'Set when the course content is available for enrolled students.'
        }),
        ('Course Content', {
            'fields': ('content',),
            'description': 'The full course material. Only enrolled students can see this.',
            'classes': ('collapse',),
        }),
    )


# ═══════════════════════════════════════════════
# Enrollment Admin
# ═══════════════════════════════════════════════
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'is_paid', 'is_approved_by_admin', 'enrollment_date')
    list_filter = ('is_paid', 'is_approved_by_admin')
    search_fields = ('student__username', 'course__title')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "student":
            kwargs["queryset"] = User.objects.filter(user_type='Student')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ═══════════════════════════════════════════════
# Exam Admin (with inline questions)
# ═══════════════════════════════════════════════
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'total_marks', 'passing_marks', 'open_date', 'close_date', 'is_published')
    list_filter = ('is_published', 'course')
    search_fields = ('title', 'course__title')
    inlines = [QuestionInline]
    fieldsets = (
        ('Exam Info', {
            'fields': ('course', 'title', 'description', 'total_marks', 'passing_marks')
        }),
        ('Schedule', {
            'fields': ('open_date', 'close_date', 'duration_minutes', 'is_published'),
            'description': 'When the exam opens/closes and how long the student has.'
        }),
    )


# ═══════════════════════════════════════════════
# Question Admin
# ═══════════════════════════════════════════════
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'order', 'text_short', 'correct_answer', 'marks')
    list_filter = ('exam',)
    search_fields = ('text',)

    def text_short(self, obj):
        return obj.text[:80] + '...' if len(obj.text) > 80 else obj.text
    text_short.short_description = 'Question'


# ═══════════════════════════════════════════════
# Exam Result Admin
# ═══════════════════════════════════════════════
@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'exam', 'marks_obtained', 'total_marks', 'passed', 'certificate_sent', 'retake_notified')
    list_filter = ('passed', 'certificate_sent', 'retake_notified')


# ═══════════════════════════════════════════════
# Certificate Admin
# ═══════════════════════════════════════════════
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'certificate_number', 'is_issued', 'email_sent', 'issued_at')
    list_filter = ('is_issued', 'email_sent')


# Register remaining models
admin.site.register(ExamAttempt)
admin.site.register(StudentAnswer)
