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
    path('notification/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
]
