from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Message, Comment
from django.http import JsonResponse
from django.apps import apps

# ---------------- Chat Room View ----------------
@login_required
def chat_room(request):
    """
    Chat page for users and admin:
    - Admin sees all messages including deleted
    - Users see only active messages
    Handles admin actions via POST:
        - delete_msg: admin soft-delete message (deleted_by_admin)
        - disappear_msg: set message to disappear after X seconds
        - update_role: change user's role
    """

    # Messages depending on user role
    if hasattr(request.user, 'is_admin') and request.user.is_admin():
        messages = Message.objects.all().order_by('-created_at')
    else:
        messages = Message.objects.filter(
            deleted_by_user=False, deleted_by_admin=False
        ).order_by('-created_at')

    # Admin actions
    if request.method == 'POST':
        action = request.POST.get('action')
        msg_id = request.POST.get('message_id')
        user_id = request.POST.get('user_id')

        # Soft-delete message by admin
        if action == 'delete_msg' and hasattr(request.user, 'is_admin') and request.user.is_admin():
            msg = Message.objects.get(id=msg_id)
            msg.deleted_by_admin = True
            msg.save()
            return JsonResponse({'status': 'deleted'})

        # Set disappear timer
        elif action == 'disappear_msg' and hasattr(request.user, 'is_admin') and request.user.is_admin():
            timer = int(request.POST.get('timer', 0))
            msg = Message.objects.get(id=msg_id)
            msg.disappear_after = timer
            msg.save()
            return JsonResponse({'status': 'timer_set'})

        # Update user role
        elif action == 'update_role' and hasattr(request.user, 'is_admin') and request.user.is_admin():
            role = request.POST.get('role')
            user_model = apps.get_model(settings.AUTH_USER_MODEL)
            user = user_model.objects.get(id=user_id)
            user.role = role
            user.save()
            return JsonResponse({'status': 'role_updated'})

    return render(request, 'Login_System/samhub_chat.html', {'messages': messages})


# ---------------- Send Message ----------------
@login_required
def send_message(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        message = Message.objects.create(user=request.user, content=content, image=image)

        profile_pic_url = getattr(request.user, 'profile_pic', None)
        profile_pic_url = profile_pic_url.url if profile_pic_url else '/static/images/default_profile.png'

        return JsonResponse({
            'id': message.id,
            'user': message.user.username,
            'profile_pic': profile_pic_url,
            'content': message.content,
            'image': message.image.url if message.image else '',
            'created_at': message.created_at.strftime('%H:%M'),
        })


# ---------------- Send Comment / Reply ----------------
@login_required
def send_comment(request):
    if request.method == 'POST':
        message_id = request.POST.get('message_id')
        content = request.POST.get('content')
        message = Message.objects.get(id=message_id)
        comment = Comment.objects.create(message=message, user=request.user, content=content)

        return JsonResponse({
            'id': comment.id,
            'user': comment.user.username,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%H:%M'),
        })


# ---------------- Delete Message (User) ----------------
@login_required
def delete_message(request, message_id):
    """
    Marks message as deleted by user (soft delete)
    Admin can also delete messages
    """
    message = Message.objects.get(id=message_id)
    if hasattr(request.user, 'is_admin') and (request.user.is_admin() or message.user == request.user):
        message.deleted_by_user = True
        message.save()
        return JsonResponse({'status': 'deleted'})

    return JsonResponse({'status': 'forbidden'})



