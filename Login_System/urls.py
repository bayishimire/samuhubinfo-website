from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    #path('dashboard/user/', views.user_dashboard, name='user_dashboard'),
    path('Login/', views.Login, name='Login'),
    path('register/', views.register_info, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('approve_admin/<int:admin_id>/', views.approve_admin, name='approve_admin'),
    # add student dashboard if needed
    # path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    
]
