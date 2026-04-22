from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, authenticate, login as auth_login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .decolotors import approved_admin_required, head_admin_required, super_or_approved_admin_required, student_required
from .models import User, OTP
from django.db.models import Q
from Job_Opportunity.models import JobApplication, Job
from scholarships.models import ScholarshipApplication, Scholarship
from projects.models import ProjectConnection, Project
from Learning_certificate.models import Enrollment, Course

User = get_user_model()
from django.utils import timezone
from datetime import timedelta
import random
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import OTP

def user_logout(request):
    logout(request)
    return redirect('home')

def register_info(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        sex = request.POST.get("sex")
        user_type = request.POST.get("user_type")  # Admin / User / Student
        password = request.POST.get("password")
        image = request.FILES.get("image")

        # 🔍 Validation
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('register')

        if len(password) < 2:
            messages.error(request, "Password must be at least 8 characters")
            return redirect('register')

        # 🔐 ADMIN POLICY: Admin still requires head approval
        if user_type == 'Admin':
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                phone=phone,
                address=address,
                sex=sex,
                user_type=user_type,
                image=image,
                is_active=False,   # cannot login until approved
                is_approved=False  # waiting approval
            )

            messages.success(
                request,
                "Admin request submitted. Waiting for Head Admin approval."
            )
            return redirect('Login')

        # ✅ USER / STUDENT: require email verification via OTP
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone=phone,
            address=address,
            sex=sex,
            user_type=user_type,
            image=image,
            is_active=False,    # locked until email verification
            is_approved=True
        )

        # create OTP and send
        otp = create_and_send_otp(request, user, purpose='verification')

        messages.success(request, "Account created. A verification code has been sent to your email.")
        return HttpResponseRedirect(reverse('verify_otp', args=[str(otp.token)]))

    return render(request, 'Login_System/register.html')




@student_required
def student_dashboard(request):
    from Learning_certificate.models import Enrollment, ExamResult, Certificate, Course

    # 1. Get student's enrollments (approved ones)
    enrollments = Enrollment.objects.filter(student=request.user, is_approved_by_admin=True)
    pending_enrollments = Enrollment.objects.filter(student=request.user, is_approved_by_admin=False)

    # 2. Get recent results
    results = ExamResult.objects.filter(enrollment__student=request.user).order_by('-completed_at')[:5]

    # 3. Get issued certificates
    certificates = Certificate.objects.filter(enrollment__student=request.user, is_issued=True)

    # 4. Recommended courses (not yet enrolled)
    enrolled_course_ids = Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
    recommended_courses = Course.objects.filter(is_active=True).exclude(id__in=enrolled_course_ids)[:3]

    context = {
        'enrollments': enrollments,
        'pending_enrollments': pending_enrollments,
        'results': results,
        'certificates': certificates,
        'recommended_courses': recommended_courses,
    }
    return render(request, 'Login_System/student_dashboard.html', context)

def Login(request):
    if request.method == "POST":
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)

        if user is not None:
            if user.user_type == 'Admin' and not user.is_approved:
                messages.error(request, "Your account is waiting for Head Admin approval.")
                return redirect('Login')

            # if user hasn't completed email verification, send/redirect to OTP
            if not user.is_active:
                otp = create_and_send_otp(request, user, purpose='verification')
                messages.info(request, "Please verify your account. A code was sent to your email.")
                return HttpResponseRedirect(reverse('verify_otp', args=[str(otp.token)]))

            auth_login(request, user)
            if user.is_superuser or (user.user_type == 'Admin' and user.is_approved):
                return redirect('dashboard_admin')
            elif user.user_type == 'Student':
                return redirect('student_dashboard')
            else:
                # Default for all other users (including 'User' type)
                return redirect('user_dashboard')

        messages.error(request, "Invalid username or password or waiting for Head Admin approval.")

    return render(request, 'Login_System/Login.html')


def create_and_send_otp(request, user, purpose='verification'):
    # prevent frequent resends: reuse recent valid un-used OTP if exists
    from django.utils import timezone
    recent = OTP.objects.filter(user=user, used=False, purpose=purpose).order_by('-created_at').first()
    if recent and (timezone.now() - recent.created_at).total_seconds() < 60:
        return recent

    code = f"{random.randint(100000, 999999)}"
    expires = timezone.now() + timedelta(minutes=10)
    otp = OTP.objects.create(user=user, code=code, expires_at=expires, purpose=purpose)

    # send email with code and link
    verify_link = request.build_absolute_uri(reverse('verify_otp', args=[str(otp.token)]))
    subject = 'Your FursaLink verification code'
    message = f"Hello {user.username},\n\nYour verification code is: {code}\nOr click the link: {verify_link}\nThis code expires in 10 minutes.\n\nIf you did not request this, ignore this message."
    send_mail(subject=subject, message=message, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[user.email], fail_silently=True)
    return otp


def verify_otp(request, token=None):
    context = {'token': token}
    otp_obj = None
    if token:
        try:
            otp_obj = OTP.objects.get(token=token)
        except OTP.DoesNotExist:
            otp_obj = None

    if request.method == 'POST':
        code = request.POST.get('code')
        token_post = request.POST.get('token')
        try:
            otp = OTP.objects.get(token=token_post, used=False)
        except OTP.DoesNotExist:
            messages.error(request, 'Invalid or already used verification link/code.')
            return redirect('register')

        if otp.is_expired():
            messages.error(request, 'Code expired. Please request a new one.')
            return redirect('register')

        if otp.code != code:
            messages.error(request, 'Incorrect code. Please try again.')
            return HttpResponseRedirect(reverse('verify_otp', args=[str(otp.token)]))

        # success
        user = otp.user
        otp.mark_used()
        user.is_active = True
        user.first_login = False
        user.save()
        messages.success(request, 'Verification successful. You can now login.')
        return redirect('Login')

    # GET: show verification form
    if otp_obj and otp_obj.is_expired():
        messages.error(request, 'Verification link has expired. Please request a new code.')
        return redirect('register')

    # include user id for resend link if available
    if otp_obj:
        context['user_id'] = otp_obj.user.id

    return render(request, 'Login_System/verify_otp.html', context)


def resend_otp(request, user_id):
    user = get_object_or_404(User, id=user_id)
    otp = create_and_send_otp(request, user)
    messages.success(request, 'A new verification code was sent (if allowed).')
    return HttpResponseRedirect(reverse('verify_otp', args=[str(otp.token)]))

@head_admin_required
def approve_admin(request, admin_id):
    admin_user = get_object_or_404(User, id=admin_id, user_type='Admin')
    admin_user.is_approved = True
    admin_user.is_active = True
    admin_user.is_staff = True  # Give them staff access for Django admin if needed
    admin_user.save()

    # 🔔 Send email notification
    send_mail(
        subject='FursaLink Admin Account Approved',
        message=f'Hello {admin_user.username}, your Admin account has been approved. You can now login.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[admin_user.email],
        fail_silently=True
    )

    messages.success(request, f"{admin_user.username} has been approved.")
    return redirect('dashboard_admin')

@super_or_approved_admin_required
def dashboard_admin(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        username = request.POST.get('username')
        email = request.POST.get('email')
        role = request.POST.get('role')
        phone = request.POST.get('phone', '')
        password = request.POST.get('password')
        image = request.FILES.get('image')

        # Create user completely approved directly from admin dashboard
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            user_type=role,
            image=image,
            is_active=True,
            is_approved=True,
            first_login=False
        )
        messages.success(request, f"User {username} successfully onboarded as {role}.")
        return redirect('dashboard_admin')

    total_users = User.objects.count()
    total_admins = User.objects.filter(user_type='Admin').count()
    pending_admins = User.objects.filter(user_type='Admin', is_approved=False)
    
    # User Directory
    all_users = User.objects.all().order_by('-date_joined')

    context = {
        'total_users': total_users,
        'total_admins': total_admins,
        'pending_admins': pending_admins,
        'all_users': all_users,
    }
    return render(request, 'Login_System/dashboard_admin.html', context)


@login_required
def dashboard_user(request):
    """
    Enhanced User Dashboard. Integrates tracking for Jobs, Scholarships, 
    Learning, and Projects.
    """
    user = request.user
    if not user.phone or not user.address or not user.sex:
        messages.info(request, "Please complete your profile details first.")
        return redirect('profile_update')

    # --- 1. Learning Progress ---
    enrollments = Enrollment.objects.filter(student=user).select_related('course')
    courses_info = []
    for enrollment in enrollments:
        courses_info.append({
            'course': enrollment.course,
            'enrolled_at': enrollment.enrolled_at,
        })

    # --- 2. Job Applications ---
    job_applications = JobApplication.objects.filter(applicant=user).select_related('job').order_by('-submitted_at')

    # --- 3. Scholarship Applications ---
    scholarship_apps = ScholarshipApplication.objects.filter(user=user).select_related('scholarship').order_by('-applied_date')

    # --- 4. Internships ---
    internships = Job.objects.all().order_by('-posted_at')
    
    internship_apps = job_applications.filter(
        Q(job__title__icontains='intern') | Q(job__description__icontains='intern')
    )

    # --- 5. Project Connections ---
    project_connections = ProjectConnection.objects.filter(user=user).select_related('project').order_by('-connected_at')

    # --- 6. Latest News (Market Updates) ---
    news_items = []
    latest_scholarships = Scholarship.objects.all().order_by('-posted_date')
    latest_jobs = Job.objects.all().order_by('-posted_at')
    
    for s in latest_scholarships:
        news_items.append({
            'type': 'Scholarship',
            'title': f"New Scholarship: {s.title}",
            'date': s.posted_date,
            'url': reverse('scholarship_detail', args=[s.id])
        })
    for j in latest_jobs:
        news_items.append({
            'type': 'Job',
            'title': f"New Opening: {j.title} at {j.company}",
            'date': j.posted_at,
            'url': reverse('job_detail', args=[j.id])
        })

    context = {
        'courses_info': courses_info,
        'job_applications': job_applications,
        'scholarship_apps': scholarship_apps,
        'internships': internships,
        'internship_apps': internship_apps,
        'project_connections': project_connections,
        'news_items': news_items,
        'all_jobs': latest_jobs,
        'all_scholarships': latest_scholarships,
    }

    return render(request, 'Login_System/user_dashboard/user_dashboard.html', context)

@login_required
def profile_update(request):
    """
    View to fill in missing profile information.
    """
    if request.method == "POST":
        user = request.user
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        user.sex = request.POST.get('sex', user.sex)
        user.date_of_birth = request.POST.get('date_of_birth', user.date_of_birth)
        user.qualification = request.POST.get('qualification', user.qualification)
        user.experience = request.POST.get('experience', user.experience)
        
        if request.FILES.get('image'):
            user.image = request.FILES.get('image')
            
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('user_dashboard')
        
    return render(request, 'Login_System/profile_update.html')
