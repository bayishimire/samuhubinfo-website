from django.contrib import admin
from .models import Message, Comment

# ---------------- Message Admin ----------------
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'content', 'created_at', 'deleted_by_user', 'disappear_after', 'parent')
    list_filter = ('deleted_by_user', 'created_at')
    search_fields = ('user__username', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

# ---------------- Comment Admin ----------------
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'message', 'content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

#admin chatbot

from django.contrib import admin
from .models import AIMessage

@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content',)
