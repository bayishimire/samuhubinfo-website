from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('Login/', views.Login, name='Login'),
    path('register/', views.register_info, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('approve_admin/<int:admin_id>/', views.approve_admin, name='approve_admin'),
    path('verify/<uuid:token>/', views.verify_otp, name='verify_otp'),
    path('resend-otp/<int:user_id>/', views.resend_otp, name='resend_otp'),
    path('dashboard/user/', views.dashboard_user, name='user_dashboard'),
    path('profile/update/', views.profile_update, name='profile_update'),
]
