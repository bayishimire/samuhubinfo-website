from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Message, Comment, MessageImage, AIMessage
from django.http import JsonResponse
from django.apps import apps
import json
from django.views.decorators.csrf import csrf_exempt
import os
try:
    import requests
except Exception:
    requests = None
from django.conf import settings

# ---------------- Chat Room View ----------------
@login_required
def chat_room(request):
    """
    Chat page for users and admin:
    - Admin sees all messages including deleted
    - Users see only active messages
    """
    # Messages depending on user role
    if request.user.is_staff or request.user.is_superuser:
        messages = Message.objects.all().order_by('created_at')
    else:
        messages = Message.objects.filter(
            deleted_by_user=False, deleted_by_admin=False
        ).order_by('created_at')

    # Admin actions
    if request.method == 'POST':
        action = request.POST.get('action')
        msg_id = request.POST.get('message_id')
        user_id = request.POST.get('user_id')

        # Soft-delete message by admin
        if action == 'delete_msg' and (request.user.is_staff or request.user.is_superuser):
            msg = Message.objects.get(id=msg_id)
            msg.deleted_by_admin = True
            msg.save()
            return JsonResponse({'status': 'deleted'})

        # Set disappear timer
        elif action == 'disappear_msg' and (request.user.is_staff or request.user.is_superuser):
            timer = int(request.POST.get('timer', 0))
            msg = Message.objects.get(id=msg_id)
            msg.disappear_after = timer
            msg.save()
            return JsonResponse({'status': 'timer_set'})

        # Update user role
        elif action == 'update_role' and (request.user.is_staff or request.user.is_superuser):
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
        parent_id = request.POST.get('parent_id')
        images = request.FILES.getlist('images')  # Handle multiple images
        
        parent_msg = None
        if parent_id:
            try:
                parent_msg = Message.objects.get(id=parent_id)
            except Message.DoesNotExist:
                parent_msg = None

        message = Message.objects.create(
            user=request.user, 
            content=content,
            parent=parent_msg
        )
        
        for img in images:
            MessageImage.objects.create(message=message, image=img)

        profile_pic_url = getattr(request.user, 'image', None)
        profile_pic_url = profile_pic_url.url if profile_pic_url else '/static/images/1.png'

        return JsonResponse({
            'status': 'success',
            'id': message.id,
            'user': message.user.username,
            'profile_pic': profile_pic_url,
            'content': message.content,
            'created_at': message.created_at.strftime('%H:%M'),
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


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
    if request.user.is_staff or request.user.is_superuser or message.user == request.user:
        message.deleted_by_user = True
        message.save()
        return JsonResponse({'status': 'deleted'})

    return JsonResponse({'status': 'forbidden'})# ---------------- AI CHATBOT VIEWS ----------------

@login_required
def ai_chat_room(request):
    """Render the AI chat interface."""
    messages = AIMessage.objects.filter(user=request.user).order_by('created_at')
    return render(request, 'Login_System/ai_chat.html', {'messages': messages})

@csrf_exempt
@login_required
def send_ai_message(request):
    """Handle AI message sending and generate response."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_msg_content = data.get('message')
        except:
            user_msg_content = request.POST.get('message')

        if not user_msg_content:
            return JsonResponse({'status': 'error', 'message': 'No message content'}, status=400)

        # Save User Message
        user_msg = AIMessage.objects.create(
            user=request.user,
            role='user',
            content=user_msg_content
        )

        # Try to build a small retrieval context from local resources
        context_docs = []
        try:
            from scholarships.models import Scholarship
            from Job_Opportunity.models import Job
        except Exception:
            Scholarship = None
            Job = None

        if Scholarship:
            qs = Scholarship.objects.filter(title__icontains=user_msg_content)[:2]
            for s in qs:
                context_docs.append(f"Scholarship: {s.title} - {getattr(s, 'short_description', '')}")

        if Job:
            qs = Job.objects.filter(title__icontains=user_msg_content)[:2]
            for j in qs:
                context_docs.append(f"Job: {j.title} - {getattr(j, 'description', '')}")

        # Try external AI provider (OpenAI) if configured
        ai_reply_content = None
        api_key = getattr(settings, 'AI_API_KEY', None) or os.environ.get('OPENAI_API_KEY')
        model = getattr(settings, 'AI_MODEL', 'gpt-3.5-turbo')

        if api_key and requests:
            try:
                system_prompt = (
                    "You are a concise assistant for the SAMHUB platform. Use any provided local resources to ground your answer. "
                    "If the user asks for resources, include a short list of relevant items with titles and short descriptions."
                )
                messages_payload = [
                    {"role": "system", "content": system_prompt},
                ]
                if context_docs:
                    docs_text = "\n\nLocal resources:\n" + "\n".join(context_docs)
                    messages_payload.append({"role": "system", "content": docs_text})

                messages_payload.append({"role": "user", "content": user_msg_content})

                resp = requests.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': model,
                        'messages': messages_payload,
                        'max_tokens': 600,
                        'temperature': 0.2,
                    },
                    timeout=30
                )
                if resp.status_code == 200:
                    j = resp.json()
                    ai_reply_content = j['choices'][0]['message']['content'].strip()
            except Exception:
                ai_reply_content = None

        # Fallback to local rule-based AI if external API unavailable
        if not ai_reply_content:
            ai_reply_content = generate_ai_response(user_msg_content, request.user)

        # Save AI Message
        ai_msg = AIMessage.objects.create(
            user=request.user,
            role='assistant',
            content=ai_reply_content,
            parent=user_msg
        )

        return JsonResponse({
            'status': 'success',
            'user_message': user_msg_content,
            'ai_message': ai_reply_content
        })
    return JsonResponse({'status': 'error'}, status=400)

def generate_ai_response(content, user):
    """
    Direct and Clear AI engine. Focuses 100% on answering the user's specific 
    request with zero fluff.
    """
    content = content.lower()
    
    # Direct Answer Logic
    if "hello" in content or "hi" in content:
        return f"Hello {user.username}! I am your SAMHUB Assistant. How can I help you with scholarships, jobs, or Irembo services today?"

    elif "irembo" in content or "register" in content:
        res = "### How to Register on Irembo 🇷🇼\n\n"
        res += "1. **Official Website:** Go to [irembo.gov.rw](https://irembo.gov.rw).\n"
        res += "2. **Search Service:** Type the service you need (e.g., Birth Certificate, Driving License).\n"
        res += "3. **Fill Form:** Enter your National ID (NID) and phone number.\n"
        res += "4. **Payment:** Pay the fee via Mobile Money or Bank.\n"
        res += "5. **Confirmation:** You will receive an SMS with your application ID."
        return res

    elif "scholarship" in content or "study" in content:
        res = "### Scholarship Search 🎓\n\n"
        res += "You can find active scholarships in our **Scholarships** section. We track:\n"
        res += "- **Full Funding:** Tuition, flights, and monthly allowance.\n"
        res += "- **Partial Funding:** Tuition waivers only.\n"
        res += "- **Local Grants:** Support for students within Rwanda.\n\n"
        res += "Go to the 'Scholarships' tab in the main menu to start your application."
        return res

    elif "job" in content or "career" in content or "opportunity" in content:
        res = "### Job Opportunities 🚀\n\n"
        res += "Our **Jobs** section is updated daily with new roles. To get hired:\n"
        res += "1. Complete your SAMHUB profile.\n"
        res += "2. Upload a clean, professional PDF Resume.\n"
        res += "3. Filter jobs by your specific skill (e.g., IT, Finance, Engineering).\n\n"
        res += "Check the 'Jobs' tab to see current openings."
        return res

    elif "help" in content:
        res = "### SAMHUB Help Center 🛠️\n\n"
        res += "I can help you with:\n"
        res += "- **Irembo Services:** Step-by-step registration guides.\n"
        res += "- **Scholarships:** Finding international and local funding.\n"
        res += "- **Job Search:** How to apply and find the best roles.\n"
        res += "- **Platform Navigation:** Finding themes and community chats."
        return res

    else:
        return f"I understand you are asking about **'{content}'**. To give you the best answer, please specify if you need help with a **Scholarship, Job, or Irembo service**, or tell me exactly what info you are looking for."
