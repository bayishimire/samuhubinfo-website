from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .models import Scholarship, ScholarshipApplication


# -------------------------------
# List all active scholarships
# -------------------------------
@login_required
def scholarship_list(request):
    scholarships = Scholarship.objects.filter(is_active=True).order_by('-posted_date')
    return render(request, 'scholarships/list.html', {
        'scholarships': scholarships
    })


# -------------------------------
# Scholarship details
# -------------------------------
@login_required
def scholarship_detail(request, pk):
    scholarship = get_object_or_404(Scholarship, pk=pk, is_active=True)

    if scholarship.status not in ['OPEN', 'EXTENDED']:
        if scholarship.status == 'UPCOMING':
            msg = "Application has not started yet. Please wait."
        elif scholarship.status in ['CLOSED', 'ENDED']:
            msg = "Applications are closed for this scholarship."
        else:
            msg = "This scholarship is not available at the moment."
        messages.warning(request, msg)
        return redirect('scholarship_list')

    return render(request, 'scholarships/detail.html', {
        'scholarship': scholarship
    })


# -------------------------------
# Download scholarship as PDF
# -------------------------------
@login_required
def scholarship_pdf(request, pk):
    scholarship = get_object_or_404(Scholarship, pk=pk, is_active=True)

    if scholarship.status not in ['OPEN', 'EXTENDED']:
        msg = "Cannot download this scholarship at this time."
        messages.warning(request, msg)
        return redirect('scholarship_list')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{scholarship.title}.pdf"'

    p = canvas.Canvas(response)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, 800, scholarship.title)
    p.setFont("Helvetica", 14)
    p.drawString(50, 770, f"University: {scholarship.university}")
    p.drawString(50, 750, f"Country: {scholarship.country}")
    p.drawString(50, 730, f"Degree Level: {scholarship.degree_level}")
    p.drawString(50, 710, f"Deadline: {scholarship.deadline}")
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 680, "Description:")
    p.setFont("Helvetica", 12)
    p.drawString(50, 660, scholarship.description[:1000])
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 620, "Eligibility:")
    p.setFont("Helvetica", 12)
    p.drawString(50, 600, scholarship.eligibility[:1000])
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 560, "Application Link:")
    p.setFont("Helvetica", 12)
    p.drawString(50, 540, scholarship.application_link)
    p.showPage()
    p.save()
    return response


# -------------------------------
# Manual scholarship application
# -------------------------------
@login_required
def apply_scholarship_manual(request, pk):
    """
    Apply manually without Django forms.
    """
    scholarship = get_object_or_404(Scholarship, pk=pk, is_active=True)

    if scholarship.status not in ['OPEN', 'EXTENDED']:
        messages.warning(request, "You cannot apply for this scholarship at this time.")
        return redirect('scholarship_list')

    if request.method == 'POST':
        try:
            application = ScholarshipApplication(
                user=request.user,
                scholarship=scholarship,
                first_name=request.POST.get('first_name'),
                middle_name=request.POST.get('middle_name'),
                last_name=request.POST.get('last_name'),
                Id=request.POST.get('ID'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                country=request.POST.get('country'),
                village=request.POST.get('village'),
                cell=request.POST.get('cell'),
                nationality=request.POST.get('nationality'),
                marital_status=request.POST.get('marital_status'),
                highest_qualification=request.POST.get('highest_qualification'),
                education_background=request.POST.get('education_background'),
                guardian_name=request.POST.get('guardian_name'),
                guardian_address=request.POST.get('guardian_address'),
                guardian_location=request.POST.get('guardian_location'),
                guardian_phone=request.POST.get('guardian_phone'),
                guardian_email=request.POST.get('guardian_email'),
                applied_date=timezone.now()
            )

            # Handle file uploads
            if 'CV_file_upload' in request.FILES:
                application.CV_file_upload = request.FILES['CV_file_upload']
            if 'application_Lettle' in request.FILES:
                application.application_Lettle = request.FILES['application_Lettle']
            if 'photo' in request.FILES:
                application.photo = request.FILES['photo']
            if 'passport' in request.FILES:
                application.passport = request.FILES['passport']
            if 'visa' in request.FILES:
                application.visa = request.FILES['visa']
            if 'bank_statement' in request.FILES:
                application.bank_statement = request.FILES['bank_statement']
            if 'other_documents' in request.FILES:
                application.other_documents = request.FILES['other_documents']

            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('scholarship_detail', pk=scholarship.pk)

        except Exception as e:
            messages.error(request, f"Error submitting application: {e}")

    return render(request, 'scholarships/apply.html', {
        'scholarship': scholarship
    })
