from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages

from Learning_certificate.models import Course, Enrollment, Exam, ExamResult, Certificate

def about(request):
    return render(request, 'Login_System/about.html')
    
# -------------------------------
# Show list of active courses
# -------------------------------
@login_required

def course_list(request):
    courses = Course.objects.filter(is_active=True)
    return render(request, 'Learning_certificate/course_list.html', {'courses': courses})

# -------------------------------
# Enroll in a course
# -------------------------------
@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user.user_type != 'Student':
        return render(request,'Learning_certificate/only_students.html')

    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    if not enrollment:
        enrollment = Enrollment.objects.create(student=request.user, course=course)
        messages.success(request, "Enrollment submitted. Await approval or payment.")
    else:
        messages.info(request, "You are already enrolled.")

    return redirect('course_list')

# -------------------------------
# Course detail page
# -------------------------------
@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=course
    ).first()

    if not enrollment or not enrollment.can_access():
        return render(request,'Learning_certificate/unllorment.html')

    exams = Exam.objects.filter(course=course)
    return render(request, 'Learning_certificate/course_detail.html', {
        'course': course,
        'enrollment': enrollment,
        'exams': exams
    })

# -------------------------------
# Take an exam
# -------------------------------
@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=exam.course
    )

    if not enrollment.can_access():
        return HttpResponseForbidden("Access denied.")

    if request.method == 'POST':
        marks = int(request.POST.get('marks'))

        ExamResult.objects.create(
            enrollment=enrollment,
            exam=exam,
            marks_obtained=marks
        )

        messages.success(request, "Exam submitted.")
        return redirect('course_detail', course_id=exam.course.id)

    return render(request, 'Learning_certificate/take_exam.html', {'exam': exam})

# -------------------------------
# Show exam results for a course
# -------------------------------
@login_required
def exam_results(request, course_id):
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course_id=course_id
    )

    results = ExamResult.objects.filter(enrollment=enrollment)

    return render(request, 'Learning_certificate/exam_results.html', {
        'results': results,
        'course': enrollment.course
    })

# -------------------------------
# View/issue certificate
# -------------------------------
@login_required
def certificate_view(request, course_id):
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course_id=course_id
    )

    certificate, _ = Certificate.objects.get_or_create(enrollment=enrollment)

    if certificate.can_issue() and not certificate.is_issued:
        certificate.issue_certificate()

    return render(request, 'Learning_certificate/certificate.html', {
        'certificate': certificate
    })


@login_required
def user_dashboard(request):
    """
    Student dashboard: shows enrolled courses, progress, certificates.
    """
    # Fetch all courses the student is enrolled in
    enrollments = Enrollment.objects.filter(student=request.user)
    
    # Prepare data: course, progress, certificate status
    courses_info = []
    for e in enrollments:
        exams = Exam.objects.filter(course=e.course)
        results = ExamResult.objects.filter(enrollment=e, exam__in=exams)
        passed_exams = results.filter(passed=True).count()
        total_exams = exams.count()
        
        # Check if certificate is issued
        certificate = Certificate.objects.filter(enrollment=e).first()
        certificate_status = certificate.is_issued if certificate else False
        
        courses_info.append({
            'enrollment': e,
            'course': e.course,
            'progress': f"{passed_exams}/{total_exams} exams passed" if total_exams else "No exams",
            'certificate_status': certificate_status
        })

    return render(request, 'Login_System/user_dashboard/user_dashboard.html', {
        'courses_info': courses_info
    })

