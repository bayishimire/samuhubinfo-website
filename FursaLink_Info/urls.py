"""
URL configuration for Fursa.Link project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.shortcuts import render
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
def home(request):
    from Job_Opportunity.models import Job
    from scholarships.models import Scholarship
    from Learning_certificate.models import Course
    from projects.models import Project
    
    latest_jobs = Job.objects.all().order_by('-posted_at')[:3]
    latest_scholarships = Scholarship.objects.all().order_by('-posted_date')[:3]
    latest_courses = Course.objects.filter(is_active=True).order_by('-created_at')[:3]
    latest_projects = Project.objects.filter(status='Published').order_by('-created_at')[:3]
    
    context = {
        'latest_jobs': latest_jobs,
        'latest_scholarships': latest_scholarships,
        'latest_courses': latest_courses,
        'latest_projects': latest_projects,
    }
    return render(request, 'Login_System/home.html', context)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    
    path('', include('Login_System.urls')),
     path('learn/', include('Learning_certificate.urls')),
     path('scholarship/', include('scholarships.urls')),
     path('projects/', include('projects.urls')),
     path('', include('Job_Opportunity.urls')),
     path('',include('FursaLink_ChatBox.urls')),
     path('accounts/', include('allauth.urls')),
    
    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

