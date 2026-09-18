from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("id", "role", "content", "citations", "out_of_domain", "created_at")
        read_only_fields = fields


class ConversationListSerializer(serializers.ModelSerializer):
    ultimo_mensaje = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "titulo", "created_at", "updated_at", "ultimo_mensaje")
        read_only_fields = fields

    def get_ultimo_mensaje(self, obj: Conversation) -> str | None:
        last = obj.messages.order_by("-created_at").first()
        return last.content[:120] if last else None


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ("id", "titulo", "created_at", "updated_at", "messages")
        read_only_fields = fields


class ChatRequestSerializer(serializers.Serializer):
    query = serializers.CharField(allow_blank=True, trim_whitespace=False)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
