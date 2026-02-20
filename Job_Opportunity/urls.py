
from django.urls import path
from . import views

urlpatterns = [
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/add/', views.add_job, name='add_job'),  # Admin add job
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('jobs/<int:job_id>/applications/', views.view_applications, name='view_applications'),

    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('jobs/<int:job_id>/download/', views.download_support, name='download_support'),
]
