import html
import re

def markdown_to_lotus_html(text: str) -> str:
    """Convert common Markdown/MarkdownV2 into the subset of HTML rendered by Lotus Chat.
    
    Lotus Chat displays MarkdownV2 escape characters literally and renders HTML entities.
    Supported tags in Lotus: <b>, <i>, <code>, <pre>, and <a href="...">.
    Tags like <s> and <blockquote> degrade gracefully to plain text.
    """
    if not isinstance(text, str) or not text:
        return text

    try:
        placeholders: list[str] = []

        def protect(val: str) -> str:
            key = f"\x00LOTUS{len(placeholders)}\x00"
            placeholders.append(val)
            return key

        # 1. Strip raw MarkdownV2 escapes (e.g. 1\. -> 1.)
        cleaned = re.sub(r"\\([_*\[\]()~`>#+\-=|{}.!\\])", r"\1", text)

        # 2. Protect fenced code blocks (```...```) and inline code (`...`)
        cleaned = re.sub(
            r"```(?:[A-Za-z0-9_+-]+)?\n?([\s\S]*?)```",
            lambda m: protect("<pre>" + html.escape(m.group(1).rstrip("\n")) + "</pre>"),
            cleaned,
        )
        cleaned = re.sub(
            r"`([^`\n]+)`",
            lambda m: protect("<code>" + html.escape(m.group(1)) + "</code>"),
            cleaned,
        )

        # 3. HTML escape remaining plain text
        cleaned = html.escape(cleaned, quote=False)

        # 4. Convert markdown formatting to HTML tags
        cleaned = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', cleaned)
        cleaned = re.sub(r"\*\*([^*\n]+)\*\*", r"<b>\1</b>", cleaned)
        cleaned = re.sub(r"__([^_\n]+)__", r"<b>\1</b>", cleaned)
        cleaned = re.sub(r"~~([^~\n]+)~~", r"<s>\1</s>", cleaned)
        cleaned = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"<i>\1</i>", cleaned)
        cleaned = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<i>\1</i>", cleaned)
        cleaned = re.sub(r"(?m)^&gt; ?(.*)$", r"<blockquote>\1</blockquote>", cleaned)

        # 5. Restore protected code blocks
        for i, val in enumerate(placeholders):
            cleaned = cleaned.replace(f"\x00LOTUS{i}\x00", val)

        return cleaned
    except Exception:
        return text
