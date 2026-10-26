from typing import TypedDict


class MessagesRoles(TypedDict):
    user: str
    ai: str


MESSAGES_ROLES: MessagesRoles = {"user": "USER", "ai": "AI"}
