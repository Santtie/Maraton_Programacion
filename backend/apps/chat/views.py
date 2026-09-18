import json

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rag.services.pipeline import RAGPipeline

from .models import Conversation
from .serializers import (
    ChatRequestSerializer,
    ConversationDetailSerializer,
    ConversationListSerializer,
    MessageSerializer,
)
from .services.conversation import get_or_create_conversation, save_turn


class ConversationListView(generics.ListAPIView):
    """GET /api/chat/conversations/ -> historial persistente del usuario (reto extra E10)."""

    serializer_class = ConversationListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)


class ConversationDetailView(generics.RetrieveDestroyAPIView):
    """GET/DELETE /api/chat/conversations/<id>/"""

    serializer_class = ConversationDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)


class ChatMessageView(APIView):
    """POST /api/chat/message/ {query, conversation_id?} -> respuesta RAG completa (JSON)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data["query"]
        conversation_id = serializer.validated_data.get("conversation_id")

        conversation = get_or_create_conversation(request.user, conversation_id, query)

        pipeline = RAGPipeline()
        result = pipeline.answer(query)

        assistant_message = save_turn(conversation, query, result.answer, result.citations, result.out_of_domain)

        return Response(
            {
                "conversation_id": conversation.id,
                "message": MessageSerializer(assistant_message).data,
            },
            status=status.HTTP_200_OK,
        )


class ChatStreamView(APIView):
    """POST /api/chat/stream/ {query, conversation_id?} -> Server-Sent Events (reto extra E9).

    El frontend debe leer la respuesta con fetch + ReadableStream (no se puede usar
    EventSource nativo del navegador porque este endpoint requiere POST + header
    Authorization con el JWT)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data["query"]
        conversation_id = serializer.validated_data.get("conversation_id")

        conversation = get_or_create_conversation(request.user, conversation_id, query)
        pipeline = RAGPipeline()

        def event_stream():
            full_text = []
            yield f"event: conversation\ndata: {json.dumps({'conversation_id': conversation.id})}\n\n"
            citations, out_of_domain = [], False
            for event in pipeline.stream_answer(query):
                if event["type"] == "token":
                    full_text.append(event["text"])
                    yield f"data: {json.dumps({'type': 'token', 'text': event['text']})}\n\n"
                elif event["type"] == "done":
                    citations, out_of_domain = event["citations"], event["out_of_domain"]
                    yield f"data: {json.dumps({'type': 'done', 'citations': citations, 'out_of_domain': out_of_domain})}\n\n"
            save_turn(conversation, query, "".join(full_text), citations, out_of_domain)

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
