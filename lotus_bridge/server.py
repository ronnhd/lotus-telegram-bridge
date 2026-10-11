import os
import logging
from typing import Any
import httpx
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse

from lotus_bridge.converter import markdown_to_lotus_html
from lotus_bridge.normalizer import normalize_inbound_update
from lotus_bridge.registry import registry

# Logger setup
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
logger = logging.getLogger("lotus_bridge")

LOTUS_API_BASE = os.environ.get("LOTUS_API_BASE", "https://bot.lotuschat.vn").rstrip("/")
TARGET_BOT_WEBHOOK_URL = os.environ.get("TARGET_BOT_WEBHOOK_URL", "").strip()
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "").strip()

raw_allowed = os.environ.get("ALLOWED_USERS", "").strip()
ALLOWED_USERS: set[int] = {int(x.strip()) for x in raw_allowed.split(",") if x.strip().isdigit()}

app = FastAPI(
    title="Lotus Telegram Bridge",
    description="Bidirectional protocol bridge enabling standard Telegram bot frameworks to operate seamlessly on Lotus Chat.",
    version="1.0.0",
)

http_client = httpx.AsyncClient(timeout=30.0)


@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "lotus-telegram-bridge"}


# ---------------------------------------------------------------------------
# 1. INBOUND WEBHOOK (Lotus -> Bridge -> Your Bot)
# ---------------------------------------------------------------------------
@app.post("/webhook")
@app.post("/telegram")
async def inbound_webhook(request: Request):
    """Receive incoming webhook updates from Lotus Chat server."""
    # 1. Secret header verification (Lotus sends Secret: <token>)
    if WEBHOOK_SECRET:
        secret_hdr = request.headers.get("Secret") or request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret_hdr != WEBHOOK_SECRET:
            logger.warning("Rejected webhook: Invalid secret token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid secret token")

    try:
        payload = await request.json()
    except Exception as exc:
        logger.error(f"Failed to parse inbound JSON: {exc}")
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)

    # 2. Normalize payload
    normalized, sender_id = normalize_inbound_update(payload)

    # 3. Private DM Allowlist check
    if ALLOWED_USERS and sender_id is not None:
        msg = payload.get("message") or {}
        chat = msg.get("chat") or {}
        if chat.get("type") == "private" and sender_id not in ALLOWED_USERS:
            logger.info(f"Dropped DM from non-allowlisted sender: {sender_id}")
            return {"ok": True, "detail": "dropped_by_allowlist"}

    # 4. Forward to backend bot if configured
    if not TARGET_BOT_WEBHOOK_URL:
        logger.debug("No TARGET_BOT_WEBHOOK_URL configured; acknowledged payload.")
        return {"ok": True}

    headers = {"Content-Type": "application/json"}
    if WEBHOOK_SECRET:
        headers["X-Telegram-Bot-Api-Secret-Token"] = WEBHOOK_SECRET

    try:
        resp = await http_client.post(
            TARGET_BOT_WEBHOOK_URL,
            json=normalized,
            headers=headers,
            timeout=15.0,
        )
        return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))
    except Exception as exc:
        logger.error(f"Failed to forward update to {TARGET_BOT_WEBHOOK_URL}: {exc}")
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=502)


# ---------------------------------------------------------------------------
# 2. OUTBOUND API INTERCEPTOR (Your Bot -> Bridge -> Lotus API)
# ---------------------------------------------------------------------------
@app.api_route("/bot{token}/{method}", methods=["GET", "POST"])
async def outbound_api_call(token: str, method: str, request: Request):
    """Intercept outbound Telegram Bot API calls, adapt Lotus quirks, and forward."""
    upstream_url = f"{LOTUS_API_BASE}/bot{token}/{method}"

    # Handle getFile interception
    if method == "getFile":
        file_id = request.query_params.get("file_id")
        if not file_id and request.method == "POST":
            try:
                body = await request.json()
                file_id = body.get("file_id")
            except Exception:
                form = await request.form()
                file_id = form.get("file_id")

        if file_id:
            cdn_url = registry.get(str(file_id))
            if cdn_url:
                logger.info(f"Emulating getFile for file_id={file_id} from cached CDN link")
                return {
                    "ok": True,
                    "result": {
                        "file_id": str(file_id),
                        "file_unique_id": str(file_id),
                        "file_path": cdn_url,
                    },
                }

    content_type = request.headers.get("content-type", "")

    # Handle JSON requests
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            body = {}

        # Auto-convert Markdown to HTML for sendMessage / editMessageText
        if method in ("sendMessage", "editMessageText") and "text" in body:
            body["text"] = markdown_to_lotus_html(body["text"])
            body["parse_mode"] = "HTML"

        # Media field mapping
        for media_field in ("photo", "document", "voice", "video", "audio"):
            if media_field in body:
                body["file"] = body.pop(media_field)

        resp = await http_client.post(upstream_url, json=body)
        return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))

    # Handle Multipart Form Data (file uploads)
    elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        data_fields: dict[str, Any] = {}
        files_to_send: list[tuple] = []

        for key, value in form.items():
            # Rename media fields to 'file'
            target_key = "file" if key in ("photo", "document", "voice", "video", "audio") else key

            if hasattr(value, "file"):  # UploadFile object
                file_bytes = await value.read()
                files_to_send.append(("file", (value.filename, file_bytes, value.content_type)))
            else:
                # Text markdown formatting
                if method in ("sendMessage", "editMessageText") and target_key == "text":
                    value = markdown_to_lotus_html(str(value))
                    data_fields["parse_mode"] = "HTML"
                data_fields[target_key] = value

        if files_to_send:
            resp = await http_client.post(upstream_url, data=data_fields, files=files_to_send)
        else:
            resp = await http_client.post(upstream_url, data=data_fields)

        return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))

    # Default proxy for other HTTP methods/types
    body = await request.body()
    resp = await http_client.request(
        method=request.method,
        url=upstream_url,
        params=request.query_params,
        content=body,
        headers={k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")},
    )
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))
