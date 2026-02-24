from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string

from .models import (
    Course, Enrollment, Exam, Question,
    ExamAttempt, StudentAnswer, ExamResult, Certificate
)


# ── Helper: send email safely ──
def _send_email_safe(subject, message, recipient_list, html_message=None):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=True,
        )
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════
# ABOUT
# ═══════════════════════════════════════════════
def about(request):
    return render(request, 'Login_System/about.html')


# ═══════════════════════════════════════════════
# COURSE LIST — visible to everyone, enroll for students
# ═══════════════════════════════════════════════
def course_list(request):
    """Everyone can see courses. Only logged-in students can enroll."""
    courses = Course.objects.filter(is_active=True)

    # If user is logged in, attach enrollment status
    enrollment_map = {}
    if request.user.is_authenticated:
        enrollments = Enrollment.objects.filter(student=request.user)
        enrollment_map = {e.course_id: e for e in enrollments}

    courses_data = []
    for course in courses:
        enrollment = enrollment_map.get(course.id)
        courses_data.append({
            'course': course,
            'enrolled': enrollment is not None,
            'can_access': enrollment.can_access() if enrollment else False,
            'enrollment': enrollment,
        })

    return render(request, 'Learning_certificate/course_list.html', {
        'courses_data': courses_data,
    })


# ═══════════════════════════════════════════════
# ENROLL IN COURSE — students only
# ═══════════════════════════════════════════════
@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user.user_type != 'Student':
        messages.error(request, "Only students can enroll in courses.")
        return redirect('course_list')

    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user, course=course
    )

    if created:
        # Auto-approve free courses
        if course.price == 0:
            enrollment.is_paid = True
            enrollment.is_approved_by_admin = True
            enrollment.save()
            messages.success(request, f"You are now enrolled in '{course.title}'! Start learning.")
        else:
            messages.success(request, f"Enrollment submitted for '{course.title}'. Awaiting approval/payment.")
    else:
        messages.info(request, "You are already enrolled in this course.")

    return redirect('course_list')


# ═══════════════════════════════════════════════
# COURSE DETAIL — only enrolled students see content
# ═══════════════════════════════════════════════
@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    enrollment = Enrollment.objects.filter(
        student=request.user, course=course
    ).first()

    if not enrollment or not enrollment.can_access():
        messages.error(request, "You need to be enrolled and approved to access this course.")
        return redirect('course_list')

    exams = course.exams.filter(is_published=True)

    # Get results for this student
    results_map = {}
    for exam in exams:
        result = ExamResult.objects.filter(
            enrollment=enrollment, exam=exam
        ).first()
        results_map[exam.id] = result

    # Check if student has an active attempt
    attempts_map = {}
    for exam in exams:
        attempt = ExamAttempt.objects.filter(
            enrollment=enrollment, exam=exam
        ).first()
        attempts_map[exam.id] = attempt

    return render(request, 'Learning_certificate/course_detail.html', {
        'course': course,
        'enrollment': enrollment,
        'exams': exams,
        'results_map': results_map,
        'attempts_map': attempts_map,
    })


# ═══════════════════════════════════════════════
# START EXAM — begin timed exam
# ═══════════════════════════════════════════════
@login_required
def start_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    enrollment = get_object_or_404(
        Enrollment, student=request.user, course=exam.course
    )

    if not enrollment.can_access():
        return HttpResponseForbidden("Access denied.")

    # Check if exam is open
    if not exam.is_open():
        messages.error(request, "This exam is not currently open.")
        return redirect('course_detail', course_id=exam.course.id)

    # Check if already submitted
    existing_result = ExamResult.objects.filter(
        enrollment=enrollment, exam=exam
    ).first()
    if existing_result:
        messages.info(request, "You have already completed this exam.")
        return redirect('exam_result_detail', result_id=existing_result.id)

    # Get or create attempt
    attempt, created = ExamAttempt.objects.get_or_create(
        enrollment=enrollment, exam=exam
    )

    if attempt.is_submitted:
        messages.info(request, "You have already submitted this exam.")
        return redirect('course_detail', course_id=exam.course.id)

    # Check time expiry
    if attempt.is_expired() and not attempt.is_submitted:
        # Auto-submit with whatever they answered
        return redirect('submit_exam', exam_id=exam.id)

    questions = exam.questions.all()

    # Get existing answers
    existing_answers = {}
    for ans in StudentAnswer.objects.filter(attempt=attempt):
        existing_answers[ans.question_id] = ans.selected_answer

    return render(request, 'Learning_certificate/take_exam.html', {
        'exam': exam,
        'attempt': attempt,
        'questions': questions,
        'existing_answers': existing_answers,
        'time_remaining': int(attempt.time_remaining()),
    })


# ═══════════════════════════════════════════════
# SAVE ANSWER — AJAX endpoint to save each answer
# ═══════════════════════════════════════════════
@login_required
def save_answer(request, exam_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    exam = get_object_or_404(Exam, id=exam_id)
    enrollment = get_object_or_404(
        Enrollment, student=request.user, course=exam.course
    )
    attempt = get_object_or_404(
        ExamAttempt, enrollment=enrollment, exam=exam, is_submitted=False
    )

    question_id = request.POST.get('question_id')
    answer = request.POST.get('answer')

    question = get_object_or_404(Question, id=question_id, exam=exam)

    StudentAnswer.objects.update_or_create(
        attempt=attempt,
        question=question,
        defaults={'selected_answer': answer}
    )

    return JsonResponse({'status': 'saved'})


# ═══════════════════════════════════════════════
# SUBMIT EXAM — grade and generate result
# ═══════════════════════════════════════════════
@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    enrollment = get_object_or_404(
        Enrollment, student=request.user, course=exam.course
    )
    attempt = get_object_or_404(
        ExamAttempt, enrollment=enrollment, exam=exam, is_submitted=False
    )

    # If POST, save final answers first
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('question_'):
                q_id = key.replace('question_', '')
                try:
                    question = Question.objects.get(id=q_id, exam=exam)
                    StudentAnswer.objects.update_or_create(
                        attempt=attempt,
                        question=question,
                        defaults={'selected_answer': value}
                    )
                except Question.DoesNotExist:
                    pass

    # Grade the exam
    answers = StudentAnswer.objects.filter(attempt=attempt)
    total_marks = 0
    marks_obtained = 0

    for question in exam.questions.all():
        total_marks += question.marks
        answer = answers.filter(question=question).first()
        if answer and answer.is_correct():
            marks_obtained += question.marks

    # Mark attempt as submitted
    attempt.is_submitted = True
    attempt.submitted_at = timezone.now()
    attempt.save()

    # Create result
    result, created = ExamResult.objects.get_or_create(
        enrollment=enrollment,
        exam=exam,
        attempt=attempt,
        defaults={
            'marks_obtained': marks_obtained,
            'total_marks': total_marks,
        }
    )

    if not created:
        result.marks_obtained = marks_obtained
        result.total_marks = total_marks
        result.save()

    # ── PASS: check certificate & email ──
    if result.passed:
        messages.success(
            request,
            f"🎉 Congratulations! You scored {marks_obtained}/{total_marks} and PASSED!"
        )
        _handle_pass(enrollment, result)

    # ── FAIL: send retake notification ──
    else:
        messages.warning(
            request,
            f"You scored {marks_obtained}/{total_marks}. The pass mark is {exam.passing_marks}. Please retake the course."
        )
        _handle_fail(enrollment, result)

    return redirect('exam_result_detail', result_id=result.id)


def _handle_pass(enrollment, result):
    """If all exams passed → issue certificate & email it."""
    # Check if ALL exams in the course are passed
    course = enrollment.course
    all_exams = course.exams.filter(is_published=True)

    all_passed = True
    for exam in all_exams:
        ex_result = ExamResult.objects.filter(
            enrollment=enrollment, exam=exam, passed=True
        ).first()
        if not ex_result:
            all_passed = False
            break

    if all_passed:
        # Issue certificate
        cert, _ = Certificate.objects.get_or_create(enrollment=enrollment)
        if cert.can_issue() and not cert.is_issued:
            cert.issue_certificate()

            # Send certificate email
            student = enrollment.student
            subject = f"🎓 Congratulations! Your SAMHUB Certificate for {course.title}"
            message = (
                f"Dear {student.username},\n\n"
                f"Congratulations! You have successfully passed all exams for '{course.title}'.\n\n"
                f"Certificate Number: {cert.certificate_number}\n"
                f"Issued on: {cert.issued_at}\n\n"
                f"You can download your certificate from your SAMHUB dashboard.\n\n"
                f"Keep learning!\n"
                f"— SAMHUB Team"
            )

            if _send_email_safe(subject, message, [student.email]):
                cert.email_sent = True
                cert.save()

            result.certificate_sent = True
            result.save()


def _handle_fail(enrollment, result):
    """Send retake notification via email."""
    student = enrollment.student
    exam = result.exam
    course = enrollment.course

    subject = f"📝 SAMHUB — Retake Required for {course.title}"
    message = (
        f"Dear {student.username},\n\n"
        f"Unfortunately, you did not pass the exam '{exam.title}' for the course '{course.title}'.\n\n"
        f"Your Score: {result.marks_obtained}/{result.total_marks}\n"
        f"Pass Mark: {exam.passing_marks}\n\n"
        f"Please review the course material and retake the exam when it reopens.\n\n"
        f"Don't give up!\n"
        f"— SAMHUB Team"
    )

    if _send_email_safe(subject, message, [student.email]):
        result.retake_notified = True
        result.save()


# ═══════════════════════════════════════════════
# EXAM RESULT DETAIL — show score breakdown
# ═══════════════════════════════════════════════
@login_required
def exam_result_detail(request, result_id):
    result = get_object_or_404(ExamResult, id=result_id)

    # Ensure the student can only see their own result
    if result.enrollment.student != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Access denied.")

    answers = StudentAnswer.objects.filter(attempt=result.attempt).select_related('question')

    return render(request, 'Learning_certificate/exam_result.html', {
        'result': result,
        'answers': answers,
    })


# ═══════════════════════════════════════════════
# COURSE RESULTS — all exam results for a course
# ═══════════════════════════════════════════════
@login_required
def exam_results(request, course_id):
    enrollment = get_object_or_404(
        Enrollment, student=request.user, course_id=course_id
    )

    results = ExamResult.objects.filter(enrollment=enrollment).select_related('exam')

    return render(request, 'Learning_certificate/exam_results.html', {
        'results': results,
        'course': enrollment.course,
    })


# ═══════════════════════════════════════════════
# CERTIFICATE VIEW
# ═══════════════════════════════════════════════
@login_required
def certificate_view(request, course_id):
    enrollment = get_object_or_404(
        Enrollment, student=request.user, course_id=course_id
    )

    certificate, _ = Certificate.objects.get_or_create(enrollment=enrollment)

    if certificate.can_issue() and not certificate.is_issued:
        certificate.issue_certificate()

    return render(request, 'Learning_certificate/certificate.html', {
        'certificate': certificate
    })


# ═══════════════════════════════════════════════
# USER DASHBOARD
# ═══════════════════════════════════════════════
from Job_Opportunity.models import JobApplication


@login_required
def user_dashboard(request):
    """Student dashboard: enrolled courses, progress, certificates, job apps."""
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')

    courses_info = []
    for e in enrollments:
        exams = e.course.exams.filter(is_published=True)
        results = ExamResult.objects.filter(enrollment=e, exam__in=exams)
        passed_exams = results.filter(passed=True).count()
        total_exams = exams.count()

        certificate = Certificate.objects.filter(enrollment=e).first()
        certificate_status = certificate.is_issued if certificate else False

        courses_info.append({
            'enrollment': e,
            'course': e.course,
            'passed_exams': passed_exams,
            'total_exams': total_exams,
            'progress': f"{passed_exams}/{total_exams} exams passed" if total_exams else "No exams yet",
            'certificate_status': certificate_status,
        })

    job_applications = JobApplication.objects.filter(applicant=request.user).order_by('-submitted_at')

    return render(request, 'Login_System/user_dashboard/user_dashboard.html', {
        'courses_info': courses_info,
        'job_applications': job_applications,
    })
