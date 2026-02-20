from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .decolotors import approved_admin_required, head_admin_required,super_or_approved_admin_required

User = get_user_model()

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

        # 🔐 ADMIN POLICY
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
                is_active=False,   # ❌ cannot login
                is_approved=False  # ⏳ waiting approval
            )

            messages.success(
                request,
                "Admin request submitted. Waiting for Head Admin approval."
            )
            return redirect('Login')

        # ✅ USER / STUDENT
        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone=phone,
            address=address,
            sex=sex,
            user_type=user_type,
            image=image,
            is_active=True,
            is_approved=True
        )

        messages.success(request, "Account created successfully. You can login now.")
        return redirect('Login')

    return render(request, 'Login_System/register.html')




from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.shortcuts import render, redirect

def Login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if the user is an Admin and if approval is required
            if user.user_type == 'Admin':
                if not user.is_approved:
                    messages.error(request, "Your admin account is waiting for Head Admin approval.")
                    return redirect('Login')
                if getattr(user, 'is_disabled', False):
                    messages.error(request, "Your admin account is disabled.")
                    return redirect('Login')

            # ✅ Log the user in
            auth_login(request, user)
            if user.is_superuser:  # Super Admin
                return redirect('dashboard_admin') 
            elif user.user_type == 'Admin':
                return redirect('dashboard_admin')
            elif user.user_type == 'User':
                return redirect('user_dashboard')
            elif user.user_type == 'Student':
                return redirect('user_dashboard')
            return redirect('home')

        messages.error(request, "Invalid username or password or waiting for Head Admin approval.if user_type is Admin.")

    return render(request, 'Login_System/Login.html')


from django.contrib.auth import logout
def user_logout(request):
    logout(request)
    return redirect('home')

# admin_user.is_approved = True  and send email waiting approval

@head_admin_required
def approve_admin(request, admin_id):
    from django.shortcuts import get_object_or_404
    from django.contrib import messages
    
    admin_user = get_object_or_404(User, id=admin_id, user_type='Admin')
    admin_user.is_approved = True
    admin_user.is_active = True
    admin_user.save()

    # 🔔 Send email notification
    send_mail(
        subject='SAMHUB Admin Account Approved',
        message=f'Hello {admin_user.username}, your Admin account has been approved. You can now login.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[admin_user.email],
        fail_silently=False
    )

    messages.success(request, f"{admin_user.username} has been approved.")
    return redirect('dashboard_admin')


# dashboard admin
@super_or_approved_admin_required

def dashboard_admin(request):
    # Total counts
    total_users = User.objects.count()
    total_admins = User.objects.filter(user_type='Admin').count()
    pending_admins = User.objects.filter(user_type='Admin', is_approved=False)

    context = {
        'total_users': total_users,
        'total_admins': total_admins,
        'pending_admins': pending_admins,
    }
    return render(request, 'Login_System/dashboard_admin.html', context)


