from django.urls import path
from . import views

urlpatterns = [
    # Main chat room
    path('chat/', views.chat_room, name='chat_room'),

    # Send a new message (text + optional image)
    path('chat/send/', views.send_message, name='send_message'),

    # Send a reply/comment to a message
    path('chat/comment/', views.send_comment, name='send_comment'),

    # Soft delete a message (user or admin)
    path('chat/delete/<int:message_id>/', views.delete_message, name='delete_message'),
    
    
    #chatbot
    
]
