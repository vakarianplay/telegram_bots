#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64
import json
import mimetypes
import re
from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import default as default_policy
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote_plus, urlparse
import requests
import yaml

@dataclass
class AssetConfig:
    source: str
    value: str | None

@dataclass
class AppConfig:
    host: str
    port: int
    template_path: Path
    help_path: Path
    tg_timeout: int
    base_dir: Path
    app_title: str
    icon: AssetConfig
    favicon: AssetConfig

    @classmethod
    def load(cls, path: Path) -> "AppConfig":
        if not path.exists():
            raise FileNotFoundError(f"Не найден файл конфигурации: {path}")
        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        server = raw.get("server", {})
        templates = raw.get("templates", {})
        telegram = raw.get("telegram", {})
        ui = raw.get("ui", {})
        icon = ui.get("icon", {}) if isinstance(ui, dict) else {}
        favicon = ui.get("favicon", {}) if isinstance(ui, dict) else {}

        base_dir = path.parent.resolve()
        template_path = (base_dir / templates.get("index", "templates/index.html")).resolve()
        help_path = (base_dir / templates.get("help", "templates/help.html")).resolve()

        return cls(
            host=server.get("host", "0.0.0.0"),
            port=int(server.get("port", 8080)),
            template_path=template_path,
            help_path=help_path,
            tg_timeout=int(telegram.get("request_timeout", 20)),
            base_dir=base_dir,
            app_title=ui.get("title", "RichMessage Publisher"),
            icon=AssetConfig(icon.get("source", "none"), icon.get("value")),
            favicon=AssetConfig(favicon.get("source", "none"), favicon.get("value"))
        )

@dataclass
class AssetInfo:
    href: str
    mime: str | None = None

class AssetResolver:
    SIMPLE_ICONS_BASE = "https://cdn.simpleicons.org"

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def resolve(self, cfg: AssetConfig) -> AssetInfo | None:
        source = (cfg.source or "none").lower()
        value = (cfg.value or "").strip()

        if source == "none" or not value:
            return None

        if source == "simpleicons":
            url = self._simpleicons_url(value)
            return AssetInfo(href=url, mime="image/svg+xml")

        if source == "url":
            return AssetInfo(href=value, mime=None)

        if source == "file":
            path = (self.base_dir / value).resolve() if not Path(value).is_absolute() else Path(value)
            if not path.exists():
                raise FileNotFoundError(f"Локальный файл иконки не найден: {path}")
            return AssetInfo(href=self._data_uri_from_file(path), mime=self._mime_from_path(path))

        raise ValueError(f"Неизвестный тип источника иконки: {cfg.source}")

    def _simpleicons_url(self, slug: str) -> str:
        return f"{self.SIMPLE_ICONS_BASE}/{slug}"

    def _data_uri_from_file(self, path: Path) -> str:
        mime = self._mime_from_path(path)
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{data}"

    @staticmethod
    def _mime_from_path(path: Path) -> str:
        mime, _ = mimetypes.guess_type(path.name)
        if mime:
            return mime
        if path.suffix.lower() == ".ico":
            return "image/x-icon"
        return "application/octet-stream"

class TemplateRenderer:
    def __init__(self, template_path: Path, help_path: Path, title: str,
                 icon: AssetInfo | None, favicon: AssetInfo | None):
        if not template_path.exists():
            raise FileNotFoundError(f"Не найден шаблон: {template_path}")
        if not help_path.exists():
            raise FileNotFoundError(f"Не найден файл инструкции: {help_path}")
        self.template_path = template_path
        self.help_html = help_path.read_text(encoding="utf-8")
        self.title = title
        self.icon = icon
        self.favicon = favicon

    def render(self, message_block: str = "") -> bytes:
        html = self.template_path.read_text(encoding="utf-8")
        replacements = {
            "{{app_title}}": escape(self.title),
            "{{brand_icon}}": self._icon_html(),
            "{{favicon_link}}": self._favicon_html(),
            "{{help_content}}": self.help_html,
            "{{message_block}}": message_block or ""
        }
        for needle, repl in replacements.items():
            html = html.replace(needle, repl)
        return html.encode("utf-8")

    def _icon_html(self) -> str:
        if not self.icon:
            return ""
        return (
            f"<img class='brand-icon' src='{self.icon.href}' "
            f"alt='{escape(self.title)}' loading='lazy' />"
        )

    def _favicon_html(self) -> str:
        if not self.favicon:
            return ""
        mime = self.favicon.mime or "image/png"
        return f"<link rel='icon' type='{mime}' href='{self.favicon.href}' />"

class TelegramClient:
    def __init__(self, token: str, timeout: int):
        self.token = token
        self.timeout = timeout

    def _request(self, method: str, payload: dict) -> Any:
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        resp = requests.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("description", "Telegram API error"))
        return data["result"]

    def get_profile(self) -> dict:
        result = self._request("getMe", {})
        return {
            "name": result.get("first_name", ""),
            "username": result.get("username", ""),
            "photo_url": None
        }

    def get_chat(self, chat_id: str) -> dict:
        result = self._request("getChat", {"chat_id": chat_id})
        photo_url = None
        photo = result.get("photo")
        if isinstance(photo, dict):
            file_id = photo.get("big_file_id") or photo.get("small_file_id")
            photo_url = self.get_file_url(file_id)
        return {
            "title": result.get("title") or result.get("first_name") or "",
            "type": result.get("type", ""),
            "photo_url": photo_url
        }

    def get_file_url(self, file_id: str | None) -> str | None:
        if not file_id:
            return None
        file_info = self._request("getFile", {"file_id": file_id})
        file_path = file_info.get("file_path")
        if not file_path:
            return None
        return f"https://api.telegram.org/file/bot{self.token}/{file_path}"

    def can_post(self, chat_id: str) -> bool:
        try:
            self._request("sendChatAction", {"chat_id": chat_id, "action": "typing"})
            return True
        except Exception:
            return False

    def send_rich_message(self, chat_id: str, content: str,
                          fmt: str, is_rtl: bool = False) -> dict:
        payload = {
            "chat_id": int(chat_id) if re.fullmatch(r"-?\d+", chat_id) else chat_id,
            "rich_message": {fmt: content}
        }
        if is_rtl:
            payload["rich_message"]["is_rtl"] = True
        return self._request("sendRichMessage", payload)

class ContentLoader:
    @staticmethod
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

    @staticmethod
    def detect_format(name: str) -> str:
        return "html" if name.lower().endswith((".html", ".htm")) else "markdown"

    @staticmethod
    def load_from_url(url: str) -> str:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text

class FormParser:
    @staticmethod
    def parse(handler: BaseHTTPRequestHandler) -> dict:
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

class PublisherHandler(BaseHTTPRequestHandler):
    server_version = "RichPublisher/3.1"
    renderer: TemplateRenderer = None
    config: AppConfig = None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/":
            block = "<div class='alert error'><div class='alert-title'>404</div></div>"
            self.respond(404, self.renderer.render(block))
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
            block = "<div class='alert error'><div class='alert-title'>404</div></div>"
            self.respond(404, self.renderer.render(block))

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

        client = TelegramClient(bot_token, self.config.tg_timeout)

        try:
            bot_info = client.get_profile()
            chat_info = client.get_chat(chat_id)
            can_post = client.can_post(chat_id)
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
        fields = FormParser.parse(self)
        bot_token = fields.get("bot_token", {}).get("data", b"").decode().strip()
        chat_id = fields.get("chat_id", {}).get("data", b"").decode().strip()
        source_url = fields.get("source_url", {}).get("data", b"").decode().strip()

        if not bot_token or not chat_id:
            self.respond_with_form(
                "error", "Не удалось отправить пост", "Укажите Bot API Key и Chat ID"
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
                    "error", "Не удалось отправить пост", "Файл должен быть в кодировке UTF-8"
                )
                return
            fmt = ContentLoader.detect_format(file_field["filename"])
        elif source_url:
            resolved = ContentLoader.github_blob_to_raw(source_url)
            try:
                content = ContentLoader.load_from_url(resolved)
            except requests.RequestException as exc:
                self.respond_with_form(
                    "error", "Не удалось отправить пост", f"Ошибка загрузки файла: {exc}"
                )
                return
            fmt = ContentLoader.detect_format(resolved)
        else:
            self.respond_with_form(
                "error", "Не удалось отправить пост", "Нужно выбрать файл или указать ссылку"
            )
            return

        if not content.strip():
            self.respond_with_form(
                "error", "Не удалось отправить пост", "Содержимое файла пустое"
            )
            return

        client = TelegramClient(bot_token, self.config.tg_timeout)

        try:
            result = client.send_rich_message(chat_id, content, fmt, is_rtl=False)
        except RuntimeError as exc:
            self.respond_with_form("error", "Telegram вернул ошибку", str(exc))
            return
        except requests.HTTPError as exc:
            body = exc.response.text if exc.response is not None else str(exc)
            self.respond_with_form("error", "Telegram отклонил запрос", body)
            return
        except requests.RequestException as exc:
            self.respond_with_form("error", "Не удалось отправить пост", f"Сетевая ошибка: {exc}")
            return

        message_id = result.get("message_id")
        detail = f"ID отправленного сообщения: {message_id}" if message_id else ""
        self.redirect_with_status("success", "Пост опубликован", detail)

    def respond_with_form(self, status: str | None, user_msg: str, tech_msg: str):
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
        self.respond(200, self.renderer.render(block))

    def redirect_with_status(self, status: str, user_msg: str, tech_msg: str):
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

def run_server(config_path: str = "config.yaml"):
    config = AppConfig.load(Path(config_path))
    resolver = AssetResolver(config.base_dir)
    icon_info = resolver.resolve(config.icon)
    favicon_info = resolver.resolve(config.favicon)

    renderer = TemplateRenderer(
        template_path=config.template_path,
        help_path=config.help_path,
        title=config.app_title,
        icon=icon_info,
        favicon=favicon_info
    )

    PublisherHandler.renderer = renderer
    PublisherHandler.config = config

    server = ThreadingHTTPServer((config.host, config.port), PublisherHandler)
    print(f"Server running on http://{config.host}:{config.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()

if __name__ == "__main__":
    run_server()