from apps.accounts.models import User

from ..models import Conversation, Message


def get_or_create_conversation(user: User, conversation_id: int | None, first_query: str) -> Conversation:
    if conversation_id:
        return Conversation.objects.get(pk=conversation_id, user=user)
    titulo = (first_query.strip()[:60] or "Nueva conversación")
    return Conversation.objects.create(user=user, titulo=titulo)


def save_turn(conversation: Conversation, query: str, answer: str, citations: list[dict], out_of_domain: bool) -> Message:
    Message.objects.create(conversation=conversation, role=Message.ROLE_USER, content=query)
    assistant_message = Message.objects.create(
        conversation=conversation,
        role=Message.ROLE_ASSISTANT,
        content=answer,
        citations=citations,
        out_of_domain=out_of_domain,
    )
    conversation.save(update_fields=["updated_at"])
    return assistant_message
