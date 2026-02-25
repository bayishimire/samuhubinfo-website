from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, authenticate, login as auth_login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Q, Avg, F, Sum, Max, Min
from django.db import models
from django.contrib.auth.decorators import login_required
from .decolotors import approved_admin_required, head_admin_required, super_or_approved_admin_required, student_required

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
    from Learning_certificate.models import Enrollment, ExamResult, Certificate, Course, Exam
    from .models import Notification

    # 1. Get student's enrollments (approved ones)
    enrollments = Enrollment.objects.filter(student=request.user, is_approved_by_admin=True)
    pending_enrollments = Enrollment.objects.filter(student=request.user, is_approved_by_admin=False)

    # 2. Get recent results
    results = ExamResult.objects.filter(enrollment__student=request.user).order_by('-completed_at')[:5]

    # 3. Get issued certificates
    certificates = Certificate.objects.filter(enrollment__student=request.user, is_issued=True)

    # 4. Progress Analysis & Recommendations
    progress_data = []
    recommendations = []
    available_exams = []
    
    for enrollment in enrollments:
        all_course_exams = Exam.objects.filter(course=enrollment.course, is_published=True)
        total_exams = all_course_exams.count()
        passed_exams_ids = ExamResult.objects.filter(enrollment=enrollment, passed=True).values_list('exam_id', flat=True)
        passed_exams_count = passed_exams_ids.count()
        
        progress = (passed_exams_count / total_exams * 100) if total_exams > 0 else 0
        progress_data.append({
            'course': enrollment.course.title,
            'progress': round(progress, 1)
        })

        # Find open exams not yet passed
        for exam in all_course_exams:
            if exam.id not in passed_exams_ids and exam.is_open():
                available_exams.append(exam)

        # Generate specific recommendations
        if progress < 100:
            next_exam = all_course_exams.exclude(id__in=passed_exams_ids).order_by('open_date').first()
            
            if next_exam:
                recommendations.append({
                    'type': 'Next Step',
                    'message': f"Complete the '{next_exam.title}' exam in {enrollment.course.title}.",
                    'course_id': enrollment.course.id
                })
        else:
            if not Certificate.objects.filter(enrollment=enrollment, is_issued=True).exists():
                recommendations.append({
                    'type': 'Reward',
                    'message': f"Congrats! You've finished {enrollment.course.title}. Claim your certificate now.",
                    'course_id': enrollment.course.id
                })

    # 5. Recommended courses (not yet enrolled)
    enrolled_course_ids = Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
    recommended_courses = Course.objects.filter(is_active=True).exclude(id__in=enrolled_course_ids)[:3]

    # 6. Notifications
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]

    context = {
        'enrollments': enrollments,
        'pending_enrollments': pending_enrollments,
        'results': results,
        'certificates': certificates,
        'recommended_courses': recommended_courses,
        'progress_data': progress_data,
        'recommendations': recommendations[:5], # limit to top 5
        'available_exams': available_exams,
        'notifications': unread_notifications,
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
            if user.is_superuser:  # Super Admin
                return redirect('dashboard_admin')
            elif user.user_type == 'Admin' and user.is_approved:
                return redirect('dashboard_admin')
            elif user.user_type == 'Student':
                return redirect('student_dashboard')
            elif user.user_type == 'User':
                return redirect('user_dashboard')
            return redirect('home')

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
    subject = 'Your SAMHUB verification code'
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
        subject='SAMHUB Admin Account Approved',
        message=f'Hello {admin_user.username}, your Admin account has been approved. You can now login.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[admin_user.email],
        fail_silently=True
    )

    messages.success(request, f"{admin_user.username} has been approved.")
    return redirect('dashboard_admin')

@super_or_approved_admin_required
def dashboard_admin(request):
    from scholarships.models import Scholarship, ScholarshipApplication
    from Learning_certificate.models import Course, Enrollment, Exam, ExamResult, Certificate, ExamAttempt
    from Job_Opportunity.models import JobApplication
    from SamHub_ChatBox.models import Message
    from django.db.models.functions import TruncDate

    # --- User Stats ---
    total_users = User.objects.count()
    total_admins = User.objects.filter(user_type='Admin').count()
    total_students = User.objects.filter(user_type='Student').count()
    pending_admins = User.objects.filter(user_type='Admin', is_approved=False)

    # --- Job & Scholarship Stats ---
    total_scholarships = Scholarship.objects.count()
    active_scholarships = Scholarship.objects.filter(status='OPEN').count()
    total_applications = ScholarshipApplication.objects.count()
    approved_apps = ScholarshipApplication.objects.filter(is_approved=True).count()
    rejected_apps = ScholarshipApplication.objects.filter(is_rejected=True).count()
    
    total_job_apps = JobApplication.objects.count()

    application_rate = (total_applications / total_users * 100) if total_users > 0 else 0

    # --- Course & Exam Stats ---
    total_courses = Course.objects.count()
    total_enrollments = Enrollment.objects.count()
    total_exams = Exam.objects.count()
    total_results = ExamResult.objects.count()
    
    passed_exams = ExamResult.objects.filter(passed=True).count()
    pass_rate = (passed_exams / total_results * 100) if total_results > 0 else 0
    
    total_certificates = Certificate.objects.filter(is_issued=True).count()

    # --- Real People Join Team Today ---
    today = timezone.now().date()
    users_joined_today = User.objects.filter(created_at__date=today).order_by('-created_at')

    # --- Recent Submissions ---
    recent_job_apps = JobApplication.objects.select_related('job', 'applicant').order_by('-submitted_at')[:5]
    recent_scholarship_apps = ScholarshipApplication.objects.select_related('scholarship', 'user').order_by('-applied_date')[:5]

    # --- Action Analysis (Last 7 Days) ---
    last_7_days = [timezone.now().date() - timedelta(days=i) for i in range(7)]
    last_7_days.reverse()
    
    daily_stats = []
    for day in last_7_days:
        daily_stats.append({
            'date': day.strftime('%a'),
            'regs': User.objects.filter(created_at__date=day).count(),
            'job_apps': JobApplication.objects.filter(submitted_at__date=day).count(),
            'sch_apps': ScholarshipApplication.objects.filter(applied_date__date=day).count(),
            'enrolls': Enrollment.objects.filter(enrollment_date__date=day).count(),
            'msgs': Message.objects.filter(created_at__date=day).count()
        })

    # --- Message & Duration Metrics ---
    # Duration: Sum of time spent on exams today (as a proxy for engagement)
    total_exam_time_today = ExamAttempt.objects.filter(
        submitted_at__date=today,
        started_at__date=today
    ).annotate(
        duration=F('submitted_at') - F('started_at')
    ).aggregate(total_dur=models.Sum('duration'))['total_dur']

    exam_duration_hours = 0
    if total_exam_time_today:
        exam_duration_hours = round(total_exam_time_today.total_seconds() / 3600, 2)

    messages_today = Message.objects.filter(created_at__date=today).count()

    # --- Upcoming Exams ---
    upcoming_exams = Exam.objects.filter(open_date__gte=timezone.now()).order_by('open_date')[:5]

    # --- Courses Analysis ---
    course_list = Course.objects.annotate(
        enrollment_count=Count('enrollments'),
        pass_count=Count('exams__results', filter=Q(exams__results__passed=True))
    ).order_by('-enrollment_count')[:5]

    # --- Community Stats (Placeholders) ---
    social_stats = {
        'whatsapp': 1250,
        'linkedin': 850,
        'twitter': 420,
        'instagram': 680
    }

    context = {
        'total_users': total_users,
        'total_admins': total_admins,
        'total_students': total_students,
        'pending_admins': pending_admins,
        'users_joined_today': users_joined_today,
        'recent_job_apps': recent_job_apps,
        'recent_scholarship_apps': recent_scholarship_apps,
        'daily_stats': daily_stats,
        'messages_today': messages_today,
        'exam_duration_hours': exam_duration_hours,
        'total_job_apps': total_job_apps,
        'scholarship_stats': {
            'total': total_scholarships,
            'active': active_scholarships,
            'applications': total_applications,
            'approved': approved_apps,
            'rejected': rejected_apps,
            'rate': round(application_rate, 1)
        },
        'course_stats': {
            'total_courses': total_courses,
            'total_enrollments': total_enrollments,
            'total_exams': total_exams,
            'pass_rate': round(pass_rate, 1),
            'certificates': total_certificates
        },
        'upcoming_exams': upcoming_exams,
        'course_list': course_list,
        'social_stats': social_stats,
    }
    return render(request, 'Login_System/dashboard_admin.html', context)


@login_required
def mark_notification_read(request, notification_id):
    from .models import Notification
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if notification.link:
        return redirect(notification.link)
    return redirect('student_dashboard')

@login_required
def mark_all_notifications_read(request):
    from .models import Notification
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('student_dashboard')
