
from django.urls import path
from . import views

urlpatterns = [
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/add/', views.add_job, name='add_job'),
    path('jobs/edit/<int:job_id>/', views.edit_job, name='edit_job'),
    path('jobs/delete/<int:job_id>/', views.delete_job, name='delete_job'),
    path('admin-panel/jobs/', views.admin_dashboard, name='admin_job_dashboard'),
    path('jobs/<int:job_id>/applications/', views.view_applications, name='view_applications'),
    path('applications/accept/<int:application_id>/', views.accept_application, name='accept_application'),
    path('applications/reject/<int:application_id>/', views.reject_application, name='reject_application'),

    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('jobs/<int:job_id>/download/', views.download_support, name='download_support'),
]
