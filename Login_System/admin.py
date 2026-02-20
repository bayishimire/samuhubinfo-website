from django.contrib import admin
from .models import User

# --- Admin Actions ---
@admin.action(description="Approve selected Admins")
def approve_admins(modeladmin, request, queryset):
    # Only filter Admin user_type
    admins = queryset.filter(user_type='Admin')
    admins.update(is_approved=True, is_active=True)

@admin.action(description="Disable selected Admins")
def disable_admins(modeladmin, request, queryset):
    admins = queryset.filter(user_type='Admin')
    admins.update(is_disabled=True, is_active=False)

# --- User Admin ---
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'user_type',
        'is_approved',
        'is_disabled',
        'is_active',
    )
    list_filter = (
        'user_type',
        'is_approved',
        'is_disabled',
        'is_active',
    )
    search_fields = (
        'username',
        'email',
    )

    # Actions available in admin list
    actions = [approve_admins, disable_admins]

    # -------------------------------
    # RESTRICT ACCESS TO CERTAIN FIELDS
    # -------------------------------
    def get_readonly_fields(self, request, obj=None):
        # Superuser can edit everything
        if request.user.is_superuser:
            return ()
        # Other staff/admin cannot edit sensitive fields
        return ('is_approved', 'is_disabled', 'is_active', 'is_superuser', 'user_type')

    # -------------------------------
    # LIMIT QUERYSET
    # -------------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Normal staff/admin cannot see superusers
        if request.user.is_superuser:
            return qs
        return qs.exclude(is_superuser=True)
