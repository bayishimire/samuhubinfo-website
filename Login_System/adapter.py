from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

class MySocialAccountAdapter(DefaultSocialAccountAdapter):

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        logger.error(f"Social auth error — Provider: {provider_id} | Error: {error} | Exception: {exception}")
        print(f"\n--- SOCIAL AUTH ERROR ---")
        print(f"Provider: {provider_id}")
        print(f"Error: {error}")
        print(f"Exception: {exception}")
        print(f"-------------------------\n")
        # Show user-friendly message
        messages.error(
            request,
            "Google Sign-In failed. Please check your Google credentials or try logging in with your username and password."
        )

    def pre_social_login(self, request, sociallogin):
        """Auto-connect existing user if email matches."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if sociallogin.is_existing:
            return
        email = sociallogin.account.extra_data.get('email', '')
        if email:
            try:
                user = User.objects.get(email=email)
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass


from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

class MyAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        if not user.is_authenticated:
            return super().get_login_redirect_url(request)

        # 1. Admin Redirect
        if user.user_type == 'Admin' or user.is_superuser:
            if user.is_superuser or user.is_approved:
                return reverse('dashboard_admin')
            else:
                messages.warning(request, "Your Admin account is pending Head Admin approval.")
                return reverse('home')
        
        # 2. Student Redirect
        if user.user_type == 'Student':
            return reverse('student_dashboard')

        # 3. Regular User (neither Admin nor Student)
        # Check for profile completeness first
        if not user.phone or not user.address or not user.sex:
            messages.info(request, "Welcome! Please complete your profile to continue.")
            return reverse('profile_update')
            
        return reverse('user_dashboard')
