from django.contrib import admin
from .models import Job, JobDocument, JobApplication

# Inline for multiple documents
class JobDocumentInline(admin.TabularInline):
    model = JobDocument
    extra = 1
    fields = ('file',)
    can_delete = True

# Job admin
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'posted_by', 'deadline', 'experience_required', 'posted_at')
    list_filter = ('experience_required', 'posted_at')
    search_fields = ('title', 'company', 'location')
    inlines = [JobDocumentInline]
    fields = (
        'title', 'company', 'location', 'description', 'requirements',
        'deadline', 'experience_required', 'support_document', 'image', 'posted_by'
    )

# JobApplication admin
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'job', 'applicant', 'email', 'status', 'submitted_at')
    list_filter = ('status',)
    search_fields = ('full_name', 'email', 'job__title')

# Register models
admin.site.register(Job, JobAdmin)
admin.site.register(JobApplication, JobApplicationAdmin)
admin.site.register(JobDocument)
