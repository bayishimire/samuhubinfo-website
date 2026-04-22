from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import FileResponse
from django.contrib import messages

from .models import Job, JobApplication, JobDocument

# --------------------------
# Helper: Admin Check
# --------------------------
def is_admin(user):
    return user.user_type == 'Admin' and user.is_approved or user.is_superuser

# --------------------------
# User Views
# --------------------------

# 1. List all available jobs
def job_list(request):
    from django.utils import timezone
    from django.db.models import Q
    
    # Show jobs where deadline is in the future, or there is no deadline
    now = timezone.now()
    jobs = Job.objects.filter(
        Q(deadline__isnull=True) | Q(deadline__gte=now)
    ).order_by('-posted_at')
    
    return render(request, 'Job_Opportunity/job_list.html', {'jobs': jobs})


# 2. Job details page
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'Job_Opportunity/job_detail.html', {'job': job})


# 3. Download support document (login required)
@login_required
def download_support(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if job.support_document:
        return FileResponse(
            job.support_document.open('rb'),
            as_attachment=True,
            filename=job.support_document.name
        )
    return redirect('job_detail', job_id=job.id)


@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        cover_letter = request.POST.get('cover_letter', '')
        resume_file = request.FILES.get('resume')

        errors = []

        # Always required
        if not full_name:
            errors.append("Full name is required.")
        if not email:
            errors.append("Email is required.")

        # Conditional: cover letter & resume based on job requirements
        if getattr(job, 'require_cover_letter', False) and not cover_letter:
            errors.append("Cover letter is required for this job.")
        if getattr(job, 'require_resume', True) and not resume_file:
            errors.append("Resume is required for this job.")

        # If there are errors, render the form again
        if errors:
            return render(request, 'Job_Opportunity/apply_job.html', {
                'job': job,
                'error': ' '.join(errors)
            })

        # Save the application
        JobApplication.objects.create(
            job=job,
            applicant=request.user,
            full_name=full_name,
            email=email,
            resume=resume_file,
            cover_letter=cover_letter
        )

        messages.success(request, "Your application has been submitted successfully!")
        return redirect('job_list')

    # GET request: show form
    return render(request, 'Job_Opportunity/apply_job.html', {'job': job})


# --------------------------
# Admin Views
# --------------------------

# 5. Admin: Add new job
@login_required
@user_passes_test(is_admin)
def add_job(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        company = request.POST.get('company')
        location = request.POST.get('location')
        description = request.POST.get('description')
        requirements = request.POST.get('requirements')
        deadline = request.POST.get('deadline')
        experience_required = request.POST.get('experience_required', 'NO')

        job = Job.objects.create(
            title=title,
            company=company,
            location=location,
            description=description,
            requirements=requirements,
            image=request.FILES.get('image'),
            deadline=deadline if deadline else None,
            posted_by=request.user,
            experience_required=experience_required,
            application_link=request.POST.get('application_link') or None,
        )

        files = request.FILES.getlist('support_document')
        for f in files:
          JobDocument.objects.create(job=job, file=f)

        messages.success(request, "Job posted successfully.")
        return redirect('admin_job_dashboard')

    return render(request, 'Job_Opportunity/add_job.html')

@login_required
@user_passes_test(is_admin)
def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if request.method == 'POST':
        job.title = request.POST.get('title')
        job.company = request.POST.get('company')
        job.location = request.POST.get('location')
        job.description = request.POST.get('description')
        job.requirements = request.POST.get('requirements')
        job.deadline = request.POST.get('deadline') if request.POST.get('deadline') else job.deadline
        job.experience_required = request.POST.get('experience_required', job.experience_required)
        job.application_link = request.POST.get('application_link') or job.application_link

        if request.FILES.get('image'):
            job.image = request.FILES.get('image')

        job.save()
        messages.success(request, f"Job '{job.title}' updated successfully.")
        return redirect('admin_job_dashboard')

    return render(request, 'Job_Opportunity/edit_job.html', {'job': job})

@login_required
@user_passes_test(is_admin)
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    title = job.title
    job.delete()
    messages.warning(request, f"Job '{title}' has been deleted.")
    return redirect('admin_job_dashboard')

# 6. Admin: Dashboard to manage all jobs
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    from django.db.models import Q
    from django.utils import timezone
    
    filter_type = request.GET.get('filter', 'all')
    now = timezone.now()

    if filter_type == 'active':
        jobs = Job.objects.filter(
            Q(deadline__isnull=True) | Q(deadline__gte=now)
        ).order_by('-posted_at')
    else:
        jobs = Job.objects.all().order_by('-posted_at')

    # Calculate Real-Time Analytics
    total_count = Job.objects.all().count()
    active_count = Job.objects.filter(
        Q(deadline__isnull=True) | Q(deadline__gte=now)
    ).count()
    regional_reach = Job.objects.values('location').distinct().count()

    context = {
        'jobs': jobs,
        'total_count': total_count,
        'active_count': active_count,
        'regional_reach': regional_reach,
        'current_filter': filter_type.upper()
    }
    return render(request, 'Job_Opportunity/admin_dashboard.html', context)


# 7. Admin: View all applications for a specific job
@login_required
@user_passes_test(is_admin)
def view_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    applications = job.applications.all().order_by('-submitted_at')
    return render(request, 'Job_Opportunity/view_applications.html', {
        'job': job,
        'applications': applications
    })

@login_required
@user_passes_test(is_admin)
def accept_application(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)
    application.status = 'ACCEPTED'
    application.save()
    messages.success(request, f"Application for {application.full_name} has been ACCEPTED.")
    return redirect('view_applications', job_id=application.job.id)

@login_required
@user_passes_test(is_admin)
def reject_application(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)
    application.status = 'REJECTED'
    application.save()
    messages.warning(request, f"Application for {application.full_name} has been REJECTED.")
    return redirect('view_applications', job_id=application.job.id)
