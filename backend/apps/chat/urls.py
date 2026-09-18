from django.urls import path

from .views import ChatMessageView, ChatStreamView, ConversationDetailView, ConversationListView

app_name = "chat"

urlpatterns = [
    path("message/", ChatMessageView.as_view(), name="message"),
    path("stream/", ChatStreamView.as_view(), name="stream"),
    path("conversations/", ConversationListView.as_view(), name="conversation-list"),
    path("conversations/<int:pk>/", ConversationDetailView.as_view(), name="conversation-detail"),
]
