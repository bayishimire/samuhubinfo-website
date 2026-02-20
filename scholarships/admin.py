from django.contrib import admin
from .models import Scholarship, ScholarshipApplication

# ------------------------
# Scholarship Admin
# ------------------------
@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display = ('title', 'university', 'country', 'degree_level', 'status', 'deadline')
    list_filter = ('country', 'degree_level', 'status')
    search_fields = ('title', 'university')

# ------------------------
# Scholarship Application Admin
# ------------------------
@admin.register(ScholarshipApplication)
class ScholarshipApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'first_name', 'last_name', 'email', 'phone', 'scholarship', 'applied_date', 'is_approved', 'is_rejected'
    )
    list_filter = ('scholarship', 'applied_date', 'is_approved', 'is_rejected')
    search_fields = ('first_name', 'last_name', 'email', 'scholarship__title')
    readonly_fields = ('applied_date',)
    ordering = ('-applied_date',)
