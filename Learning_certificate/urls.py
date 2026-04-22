from django.urls import path
from . import views

urlpatterns = [
    # Course browsing (public)
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),

    # Exams
    path('exams/<int:exam_id>/start/', views.start_exam, name='start_exam'),
    path('exams/<int:exam_id>/save-answer/', views.save_answer, name='save_answer'),
    path('exams/<int:exam_id>/submit/', views.submit_exam, name='submit_exam'),

    # Results & Certificate
    path('results/<int:result_id>/', views.exam_result_detail, name='exam_result_detail'),
    path('courses/<int:course_id>/results/', views.exam_results, name='exam_results'),
    path('courses/<int:course_id>/certificate/', views.certificate_view, name='certificate_view'),

    # Dashboard & About
    path('User_Dashboard/', views.user_dashboard, name='user_dashboard'),
    path('about/', views.about, name='about'),

    # Custom Admin Native URLs
    path('admin-panel/', views.admin_course_dashboard, name='admin_course_dashboard'),
    path('admin-panel/add/', views.admin_add_course, name='admin_add_course'),
    path('admin-panel/delete/<int:course_id>/', views.admin_delete_course, name='admin_delete_course'),
]
