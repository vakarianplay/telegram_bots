#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
from email.parser import BytesParser
from email.policy import default as default_policy
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
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
    server_version = "RichPublisher/1.0"

    def do_GET(self):
        if self.path == "/":
            self.respond_with_form()
        else:
            self.respond(404, render_template("<div class='alert error'>404</div>"))

    def do_POST(self):
        if self.path != "/publish":
            self.respond(404, render_template("<div class='alert error'>404</div>"))
            return

        fields = parse_form(self)
        bot_token = fields.get("bot_token", {}).get("data", b"").decode().strip()
        chat_id = fields.get("chat_id", {}).get("data", b"").decode().strip()
        source_url = fields.get("source_url", {}).get("data", b"").decode().strip()
        is_rtl = "is_rtl" in fields

        if not bot_token or not chat_id:
            self.respond_with_form("error", "Укажите Bot API Key и Chat ID")
            return

        content = None
        fmt = "markdown"

        file_field = fields.get("content_file")
        if file_field and file_field.get("filename"):
            try:
                content = file_field["data"].decode("utf-8")
            except UnicodeDecodeError:
                self.respond_with_form("error", "Файл должен быть в UTF-8")
                return
            fmt = detect_format(file_field["filename"])
        elif source_url:
            resolved = github_blob_to_raw(source_url)
            try:
                resp = requests.get(resolved, timeout=15)
                resp.raise_for_status()
            except requests.RequestException as exc:
                self.respond_with_form("error", f"Не удалось загрузить URL: {exc}")
                return
            content = resp.text
            fmt = detect_format(resolved)
        else:
            self.respond_with_form("error", "Нужно выбрать файл или указать ссылку")
            return

        if not content.strip():
            self.respond_with_form("error", "Содержимое пустое")
            return

        try:
            response = send_rich_message(bot_token, chat_id, content, fmt, is_rtl)
            response.raise_for_status()
            result = response.json()
        except requests.HTTPError as exc:
            body = exc.response.text if exc.response is not None else str(exc)
            self.respond_with_form("error", f"Telegram API ошибка: {body}")
            return
        except requests.RequestException as exc:
            self.respond_with_form("error", f"Сетевая ошибка: {exc}")
            return
        except json.JSONDecodeError:
            self.respond_with_form("error", "Некорректный ответ Telegram")
            return

        if not result.get("ok"):
            self.respond_with_form(
                "error",
                f"Telegram вернул ошибку:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
            )
            return

        message_id = result["result"]["message_id"]
        self.respond_with_form("success", f"Пост отправлен. message_id={message_id}")

    def respond_with_form(self, status: str | None = None, text: str = ""):
        if status == "success":
            block = f"<div class='alert success'>{escape(text)}</div>"
        elif status == "error":
            block = f"<div class='alert error'>{escape(text)}</div>"
        else:
            block = ""
        self.respond(200, render_template(block))

    def respond(self, status: int, body: bytes):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
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