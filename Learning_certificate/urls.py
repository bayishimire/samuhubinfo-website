from django.urls import path
from . import views

urlpatterns = [
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('exams/<int:exam_id>/take/', views.take_exam, name='take_exam'),
    path('courses/<int:course_id>/results/', views.exam_results, name='exam_results'),
    path('courses/<int:course_id>/certificate/', views.certificate_view, name='certificate_view'),
    path('User_Dashboard/', views.user_dashboard, name='user_dashboard'),
    path('about/', views.about, name='about'),
]
