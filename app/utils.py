from uuid import uuid7


def get_id():
    id = uuid7()

    return str(id)


CHAT_TITLE_MAX_LENGTH = 60


def make_chat_title(text: str):
    title = " ".join(text.split())

    if not title:
        return "Untitled chat"

    if len(title) > CHAT_TITLE_MAX_LENGTH:
        return title[:CHAT_TITLE_MAX_LENGTH].rstrip() + "…"

    return title
