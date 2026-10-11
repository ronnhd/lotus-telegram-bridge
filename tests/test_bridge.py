import unittest
from lotus_bridge.converter import markdown_to_lotus_html
from lotus_bridge.normalizer import normalize_inbound_update
from lotus_bridge.registry import registry

class TestLotusBridge(unittest.TestCase):
    def test_markdown_to_html_formatting(self):
        md = "Hello **world**, this is *italic* and `inline code` with a [link](https://example.com)."
        html = markdown_to_lotus_html(md)
        self.assertIn("<b>world</b>", html)
        self.assertIn("<i>italic</i>", html)
        self.assertIn("<code>inline code</code>", html)
        self.assertIn('<a href="https://example.com">link</a>', html)

    def test_markdownv2_escape_stripping(self):
        md = "1\\. Step one\n2\\. Step two\nPrice: $100\\!"
        html = markdown_to_lotus_html(md)
        self.assertIn("1. Step one", html)
        self.assertIn("Price: $100!", html)
        self.assertNotIn("\\.", html)

    def test_private_chat_id_rewrite(self):
        payload = {
            "update_id": 1001,
            "message": {
                "message_id": 42,
                "date": 1700000000,
                "from": {"id": 12345, "first_name": "Alice"},
                "chat": {"id": 9999999999999999, "type": "private"},
                "text": "Hello bot"
            }
        }
        normalized, sender_id = normalize_inbound_update(payload)
        msg = normalized["message"]
        self.assertEqual(sender_id, 12345)
        self.assertEqual(msg["chat"]["id"], 12345)
        self.assertFalse(msg["from"]["is_bot"])

    def test_bare_int_reply_to_message(self):
        payload = {
            "update_id": 1002,
            "message": {
                "message_id": 43,
                "from": {"id": 12345},
                "chat": {"id": -100123, "type": "group"},
                "reply_to_message": 999,
                "text": "Reply"
            }
        }
        normalized, _ = normalize_inbound_update(payload)
        reply = normalized["message"]["reply_to_message"]
        self.assertIsInstance(reply, dict)
        self.assertEqual(reply["message_id"], 999)

    def test_media_link_cdn_registration(self):
        payload = {
            "update_id": 1003,
            "message": {
                "message_id": 44,
                "from": {"id": 12345},
                "chat": {"id": 12345, "type": "private"},
                "photo": [
                    {"file_id": "photo_123", "link_cdn": "https://chat-cdn.lotus.vn/media1.jpg"}
                ]
            }
        }
        normalize_inbound_update(payload)
        self.assertEqual(registry.get("photo_123"), "https://chat-cdn.lotus.vn/media1.jpg")

if __name__ == "__main__":
    unittest.main()
