#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
from email.parser import BytesParser
from email.policy import default as default_policy
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse, quote_plus
import requests

HOST = "0.0.0.0"
PORT = 8080
TEMPLATE_PATH = Path("templates/index.html")

def github_blob_to_raw(url: str) -> str:
    parsed = urlparse(url)
    if "github.com" not in parsed.netloc or "/blob/" not in parsed.path:
        return url
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 5:
        return url
    user, repo, blob, branch, *rest = parts
    raw_path = "/".join(rest)
    return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{raw_path}"

def detect_format(filename: str) -> str:
    if filename.lower().endswith((".html", ".htm")):
        return "html"
    return "markdown"

def telegram_request(token: str, method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    resp = requests.post(url, json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("description", "Telegram API error"))
    return data["result"]

def get_file_url(token: str, file_id: str | None) -> str | None:
    if not file_id:
        return None
    result = telegram_request(token, "getFile", {"file_id": file_id})
    file_path = result.get("file_path")
    if not file_path:
        return None
    return f"https://api.telegram.org/file/bot{token}/{file_path}"

def fetch_bot_profile(token: str) -> dict:
    result = telegram_request(token, "getMe", {})
    return {
        "name": result.get("first_name", ""),
        "username": result.get("username", ""),
        "photo_url": None
    }

def fetch_chat_profile(token: str, chat_id: str) -> dict:
    result = telegram_request(token, "getChat", {"chat_id": chat_id})
    chat_info = {
        "title": result.get("title") or result.get("first_name") or "",
        "type": result.get("type", ""),
        "photo_url": None
    }
    photo = result.get("photo")
    if isinstance(photo, dict):
        file_id = photo.get("big_file_id") or photo.get("small_file_id")
        chat_info["photo_url"] = get_file_url(token, file_id)
    return chat_info

def check_can_post(token: str, chat_id: str) -> bool:
    try:
        telegram_request(token, "sendChatAction", {
            "chat_id": chat_id,
            "action": "typing"
        })
        return True
    except Exception:
        return False

def send_rich_message(bot_token: str, chat_id: str, content: str,
                      fmt: str, is_rtl: bool) -> requests.Response:
    payload = {
        "chat_id": int(chat_id) if re.fullmatch(r"-?\d+", chat_id) else chat_id,
        "rich_message": {fmt: content}
    }
    if is_rtl:
        payload["rich_message"]["is_rtl"] = True
    url = f"https://api.telegram.org/bot{bot_token}/sendRichMessage"
    return requests.post(url, json=payload, timeout=20)

def parse_form(handler: BaseHTTPRequestHandler) -> dict:
    content_type = handler.headers.get("Content-Type", "")
    length = int(handler.headers.get("Content-Length", "0"))
    body = handler.rfile.read(length)

    if "multipart/form-data" in content_type:
        if "boundary=" not in content_type:
            return {}
        boundary = content_type.split("boundary=", 1)[1].strip().strip('"')
        parser = BytesParser(policy=default_policy)
        message = parser.parsebytes(
            b"Content-Type: multipart/form-data; boundary="
            + boundary.encode()
            + b"\r\n\r\n"
            + body
        )
        fields = {}
        for part in message.iter_parts():
            disposition = part.get("Content-Disposition", "")
            if "form-data" not in disposition:
                continue
            name = part.get_param("name", header="Content-Disposition")
            if not name:
                continue
            filename = part.get_filename()
            payload = part.get_payload(decode=True) or b""
            fields[name] = {"filename": filename, "data": payload}
        return fields

    if "application/x-www-form-urlencoded" in content_type:
        data = parse_qs(body.decode("utf-8"), keep_blank_values=True)
        return {
            key: {"filename": None, "data": values[-1].encode("utf-8")}
            for key, values in data.items()
        }

    return {}

def render_template(message_block: str = "") -> bytes:
    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    return html.replace("{{message_block}}", message_block).encode("utf-8")

class PublisherHandler(BaseHTTPRequestHandler):
    server_version = "RichPublisher/2.2"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/":
            self.respond(404, render_template("<div class='alert error'><div class='alert-title'>404</div></div>"))
            return
        params = parse_qs(parsed.query)
        status = params.get("status", [None])[0]
        msg = params.get("msg", [""])[0]
        detail = params.get("detail", [""])[0]
        self.respond_with_form(status, msg, detail)

    def do_POST(self):
        if self.path == "/publish":
            self.handle_publish()
        elif self.path == "/api/check":
            self.handle_check()
        else:
            self.respond(404, render_template("<div class='alert error'><div class='alert-title'>404</div></div>"))

    def handle_check(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self.json_response(400, {"ok": False, "error": "Некорректный JSON"})
            return

        bot_token = (payload.get("bot_token") or "").strip()
        chat_id = (payload.get("chat_id") or "").strip()

        if not bot_token or not chat_id:
            self.json_response(400, {"ok": False, "error": "Укажите Bot API Key и Chat ID"})
            return

        try:
            bot_info = fetch_bot_profile(bot_token)
            chat_info = fetch_chat_profile(bot_token, chat_id)
            can_post = check_can_post(bot_token, chat_id)
        except Exception as exc:
            self.json_response(400, {"ok": False, "error": str(exc)})
            return

        self.json_response(200, {
            "ok": True,
            "bot": bot_info,
            "chat": chat_info,
            "can_post": can_post
        })

    def handle_publish(self):
        fields = parse_form(self)
        bot_token = fields.get("bot_token", {}).get("data", b"").decode().strip()
        chat_id = fields.get("chat_id", {}).get("data", b"").decode().strip()
        source_url = fields.get("source_url", {}).get("data", b"").decode().strip()

        if not bot_token or not chat_id:
            self.respond_with_form(
                "error",
                "Не удалось отправить пост",
                "Укажите Bot API Key и Chat ID"
            )
            return

        content = None
        fmt = "markdown"

        file_field = fields.get("content_file")
        if file_field and file_field.get("filename"):
            try:
                content = file_field["data"].decode("utf-8")
            except UnicodeDecodeError:
                self.respond_with_form(
                    "error",
                    "Не удалось отправить пост",
                    "Файл должен быть в кодировке UTF-8"
                )
                return
            fmt = detect_format(file_field["filename"])
        elif source_url:
            resolved = github_blob_to_raw(source_url)
            try:
                resp = requests.get(resolved, timeout=15)
                resp.raise_for_status()
            except requests.RequestException as exc:
                self.respond_with_form(
                    "error",
                    "Не удалось отправить пост",
                    f"Ошибка загрузки файла: {exc}"
                )
                return
            content = resp.text
            fmt = detect_format(resolved)
        else:
            self.respond_with_form(
                "error",
                "Не удалось отправить пост",
                "Нужно выбрать файл или указать ссылку"
            )
            return

        if not content.strip():
            self.respond_with_form(
                "error",
                "Не удалось отправить пост",
                "Содержимое файла пустое"
            )
            return

        try:
            response = send_rich_message(bot_token, chat_id, content, fmt, is_rtl=False)
            response.raise_for_status()
            result = response.json()
        except requests.HTTPError as exc:
            body = exc.response.text if exc.response is not None else str(exc)
            self.respond_with_form(
                "error",
                "Telegram отклонил запрос",
                body
            )
            return
        except requests.RequestException as exc:
            self.respond_with_form(
                "error",
                "Не удалось отправить пост",
                f"Сетевая ошибка: {exc}"
            )
            return
        except json.JSONDecodeError:
            self.respond_with_form(
                "error",
                "Не удалось отправить пост",
                "Ответ Telegram не похож на JSON"
            )
            return

        if not result.get("ok"):
            self.respond_with_form(
                "error",
                "Telegram вернул ошибку",
                json.dumps(result, ensure_ascii=False, indent=2)
            )
            return

        message_id = result["result"]["message_id"]
        self.redirect_with_status(
            "success",
            "Пост опубликован",
            f"ID отправленного сообщения: {message_id}"
        )

    def respond_with_form(self, status: str | None = None,
                          user_msg: str = "", tech_msg: str = ""):
        block = ""
        if status == "success":
            title = user_msg or "Операция выполнена успешно"
            block = (
                "<div class='alert success'>"
                f"<div class='alert-title'>{escape(title)}</div>"
            )
            if tech_msg:
                block += f"<div class='alert-meta'>{escape(tech_msg)}</div>"
            block += "</div>"
        elif status == "error":
            title = user_msg or "Не удалось выполнить действие"
            block = (
                "<div class='alert error'>"
                f"<div class='alert-title'>{escape(title)}</div>"
            )
            if tech_msg:
                block += f"<div class='alert-meta'>{escape(tech_msg)}</div>"
            block += "</div>"
        data = render_template(block)
        self.respond(200, data)

    def redirect_with_status(self, status: str, user_msg: str, tech_msg: str = ""):
        location = (
            "/?status="
            f"{quote_plus(status or '')}"
            f"&msg={quote_plus(user_msg or '')}"
            f"&detail={quote_plus(tech_msg or '')}"
        )
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

    def respond(self, status: int, body: bytes):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def json_response(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

def run_server():
    server = ThreadingHTTPServer((HOST, PORT), PublisherHandler)
    print(f"Server running on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()

if __name__ == "__main__":
    if not TEMPLATE_PATH.exists():
        raise SystemExit("Не найден templates/index.html")
    run_server()