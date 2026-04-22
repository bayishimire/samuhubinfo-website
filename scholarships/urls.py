from django.urls import path
from . import views





urlpatterns = [
    path('scholarships/', views.scholarship_list, name='scholarship_list'),
    path('scholarship/<int:pk>/', views.scholarship_detail, name='scholarship_detail'),
    path('scholarship/<int:pk>/pdf/', views.scholarship_pdf, name='scholarship_pdf'),
    path('<int:pk>/apply_manual/', views.apply_scholarship_manual, name='apply_scholarship_manual'),

    # Custom Admin Native URLs
    path('admin-panel/', views.admin_scholarship_dashboard, name='admin_scholarship_dashboard'),
    path('admin-panel/add/', views.admin_add_scholarship, name='admin_add_scholarship'),
    path('admin-panel/delete/<int:pk>/', views.admin_delete_scholarship, name='admin_delete_scholarship'),
]
