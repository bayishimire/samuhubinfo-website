from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Course, Enrollment, Exam, ExamResult, Certificate

User = get_user_model()

# Custom Enrollment admin
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'is_paid', 'is_approved_by_admin', 'enrollment_date')
    
    # Filter the student dropdown to only users with user_type='Student'
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "student":
            kwargs["queryset"] = User.objects.filter(user_type='Student')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Register models
admin.site.register(Course)
admin.site.register(Enrollment, EnrollmentAdmin)  # Use custom admin
admin.site.register(Exam)
admin.site.register(ExamResult)
admin.site.register(Certificate)
