from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import FileResponse

from .models import Job, JobApplication, JobDocument

# --------------------------
# Helper: Admin Check
# --------------------------
def is_admin(user):
    return user.is_superuser

# --------------------------
# User Views
# --------------------------

# 1. List all available jobs
def job_list(request):
    jobs = Job.objects.all().order_by('-posted_at')
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

        # Redirect to jobs list after successful application
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
        image = request.FILES.get('image')
        experience_required = request.POST.get('experience_required', 'NO')

        if not title or not company:
            error = "Title and Company are required."
            return render(request, 'Job_Opportunity/add_job.html', {'error': error})

        # Create Job object first
        job = Job.objects.create(
            title=title,
            company=company,
            location=location,
            description=description,
            requirements=requirements,
            image=request.FILES.get('image'),
            deadline=deadline if deadline else None,
            posted_by=request.user,
            
            experience_required=experience_required
        )

        # Handle multiple support documents
        files = request.FILES.getlist('support_document')
        for f in files:
          JobDocument.objects.create(job=job, file=f)

        return redirect('admin_dashboard')

    return render(request, 'Job_Opportunity/add_job.html')



# 6. Admin: Dashboard to manage all jobs
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    jobs = Job.objects.all().order_by('-posted_at')
    return render(request, 'Job_Opportunity/admin_dashboard.html', {'jobs': jobs})


# 7. Admin: View all applications for a specific job
@login_required
@user_passes_test(is_admin)
def view_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    applications = job.applications.all()
    return render(request, 'Job_Opportunity/view_applications.html', {
        'job': job,
        'applications': applications
    })
