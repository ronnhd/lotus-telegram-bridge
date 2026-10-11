from typing import Any, Tuple
from lotus_bridge.registry import registry

def normalize_inbound_update(data: dict[str, Any]) -> Tuple[dict[str, Any], int | None]:
    """Normalize inbound Lotus Chat webhook payload to strict Telegram Bot API specs.
    
    Fixes:
    1. Private chat rewrite: Lotus sets chat.id to an internal 16-digit conversation ID.
       When replying, Lotus server ignores sendMessage to that ID. We rewrite chat.id = from.id.
    2. Missing User.is_bot: Lotus omits is_bot. We inject is_bot=False if missing.
    3. Bare-int reply_to_message: Lotus sends reply_to_message as an integer message_id.
       We wrap it in a proper Message object stub {"message_id": <int>}.
    4. Media CDN caching: Extract link_cdn and register file_id -> link_cdn for getFile emulation.
    
    Returns:
        (normalized_data, sender_user_id)
    """
    if not isinstance(data, dict):
        return data, None

    msg = data.get("message") or data.get("edited_message")
    sender_id = None

    if isinstance(msg, dict):
        sender = msg.get("from")
        if isinstance(sender, dict):
            sender_id = sender.get("id")
            if "is_bot" not in sender:
                sender["is_bot"] = False

        # 1. Private chat ID rewrite
        chat = msg.get("chat")
        if isinstance(chat, dict):
            chat_type = chat.get("type")
            if chat_type == "private" and sender_id is not None:
                chat["id"] = sender_id

        # 2. Bare integer reply_to_message
        reply_to = msg.get("reply_to_message")
        if isinstance(reply_to, int):
            msg["reply_to_message"] = {
                "message_id": reply_to,
                "date": msg.get("date", 0),
                "chat": chat or {},
            }

        # 3. Cache media link_cdn
        # Check photo array
        photos = msg.get("photo")
        if isinstance(photos, list):
            for p in photos:
                if isinstance(p, dict) and p.get("file_id") and p.get("link_cdn"):
                    registry.register(str(p["file_id"]), p["link_cdn"])

        # Check document, voice, video, audio
        for media_key in ("document", "voice", "video", "audio"):
            media_item = msg.get(media_key)
            if isinstance(media_item, dict) and media_item.get("file_id") and media_item.get("link_cdn"):
                registry.register(str(media_item["file_id"]), media_item["link_cdn"])

    return data, sender_id
