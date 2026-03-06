"""
Publish a prepared article to a WeChat Official Account.

This script reads a local text article, converts it into simple WeChat-friendly
HTML, optionally uploads a cover image, creates a draft, and can submit it for
publishing.

It targets the WeChat Official Account draft/freepublish flow and requires an
account with the corresponding API permissions.
"""

from __future__ import annotations

import argparse
import html
import json
import mimetypes
import os
from pathlib import Path
import re
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"
FREEPUBLISH_SUBMIT_URL = "https://api.weixin.qq.com/cgi-bin/freepublish/submit"
FREEPUBLISH_GET_URL = "https://api.weixin.qq.com/cgi-bin/freepublish/get"
MATERIAL_ADD_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"

DEFAULT_AUTHOR = "Knowledge Extraction"
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_POLL_INTERVAL_SECONDS = 5
DEFAULT_DIGEST_LENGTH = 120
DRY_RUN_THUMB_MEDIA_ID = "DRY_RUN_THUMB_MEDIA_ID"

MAIN_HEADING_RE = re.compile(r"^[一二三四五六七八九十]+、")
SUB_HEADING_RE = re.compile(r"^(?:\d+\.\s*|第\s*\d+\s*步[:：]?)")
EMPHASIS_RE = re.compile(r"^[^。！？!?]{1,40}[：:]?$")


class WeChatPublisherError(RuntimeError):
    """Raised when the WeChat API returns an error or the input is invalid."""


@dataclass
class ArticleContent:
    """Parsed article content from a local text file."""

    title: str
    body_text: str


def load_env_file(env_path: str = ".env") -> None:
    """Load KEY=VALUE pairs from a .env-like file into os.environ."""
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")

        if key and key not in os.environ:
            os.environ[key] = value


def first_non_empty(*values: Optional[str], default: Optional[str] = None) -> Optional[str]:
    """Return the first non-empty string value."""
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def read_article_file(article_path: str, override_title: Optional[str] = None) -> ArticleContent:
    """Read a text article and treat the first non-empty line as the title."""
    path = Path(article_path)
    if not path.exists():
        raise WeChatPublisherError(f"Article file not found: {path}")

    raw_text = path.read_text(encoding="utf-8").strip()
    if not raw_text:
        raise WeChatPublisherError(f"Article file is empty: {path}")

    lines = [line.rstrip() for line in raw_text.splitlines()]
    content_lines = [line for line in lines if line.strip()]
    if not content_lines:
        raise WeChatPublisherError(f"Article file has no usable content: {path}")

    detected_title = content_lines[0].strip()
    title = first_non_empty(override_title, detected_title)

    remaining_lines = lines[:]
    while remaining_lines and not remaining_lines[0].strip():
        remaining_lines.pop(0)
    if remaining_lines and remaining_lines[0].strip() == detected_title:
        remaining_lines.pop(0)

    body_text = "\n".join(remaining_lines).strip()
    if not body_text:
        raise WeChatPublisherError(
            "Article body is empty after removing the title line. "
            "Add article content below the title."
        )

    return ArticleContent(title=title, body_text=body_text)


def build_digest(body_text: str, max_length: int = DEFAULT_DIGEST_LENGTH) -> str:
    """Create a short digest from the article body."""
    condensed = " ".join(part.strip() for part in body_text.splitlines() if part.strip())
    return condensed[:max_length].strip()


def classify_line(line: str) -> str:
    """Classify a line so it can be rendered with simple formatting."""
    stripped = line.strip()
    if not stripped:
        return "blank"
    if MAIN_HEADING_RE.match(stripped) or stripped in {"最后想说", "最后想说：", "说明", "说明："}:
        return "heading"
    if SUB_HEADING_RE.match(stripped):
        return "subheading"
    if len(stripped) <= 40 and EMPHASIS_RE.match(stripped):
        return "emphasis"
    return "paragraph"


def render_line_as_html(line: str) -> str:
    """Render a single line into a WeChat-compatible HTML fragment."""
    stripped = line.strip()
    escaped = html.escape(stripped)
    kind = classify_line(stripped)

    if kind == "heading":
        return (
            f'<h2 style="margin:28px 0 12px; font-size:22px; '
            f'line-height:1.45; font-weight:700;">{escaped}</h2>'
        )
    if kind == "subheading":
        return (
            f'<p style="margin:18px 0 8px; font-size:18px; line-height:1.7; '
            f'font-weight:700;">{escaped}</p>'
        )
    if kind == "emphasis":
        return (
            f'<p style="margin:14px 0; font-size:17px; line-height:1.8; '
            f'font-weight:700;">{escaped}</p>'
        )
    return (
        f'<p style="margin:12px 0; font-size:16px; line-height:1.9; '
        f'color:#222222;">{escaped}</p>'
    )


def build_wechat_html(body_text: str) -> str:
    """Convert plain text into simple HTML suitable for a WeChat article."""
    html_parts = []
    for line in body_text.splitlines():
        if not line.strip():
            continue
        html_parts.append(render_line_as_html(line))

    if not html_parts:
        raise WeChatPublisherError("Article body could not be converted to HTML.")

    return "\n".join(html_parts)


def save_text_file(path: str, content: str) -> None:
    """Write a UTF-8 file, creating parent directories when needed."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def format_json(data: Dict[str, Any]) -> str:
    """Pretty-print JSON for terminal output."""
    return json.dumps(data, ensure_ascii=False, indent=2)


class WeChatOfficialAccountPublisher:
    """Minimal client for WeChat Official Account draft/publish APIs."""

    def __init__(self, app_id: str, app_secret: str, timeout: int = DEFAULT_TIMEOUT_SECONDS):
        self.app_id = app_id
        self.app_secret = app_secret
        self.timeout = timeout
        self._access_token: Optional[str] = None
        self._session = None

    def _get_session(self):
        if self._session is None:
            try:
                import requests
            except ImportError as exc:
                raise WeChatPublisherError(
                    "Missing dependency 'requests'. Install it with "
                    "`pip install -r requirements.txt`."
                ) from exc
            self._session = requests.Session()
        return self._session

    def _parse_response(self, response) -> Dict[str, Any]:
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as exc:
            raise WeChatPublisherError(
                f"WeChat API returned non-JSON response: {response.text}"
            ) from exc

        if data.get("errcode", 0) not in (0, None):
            raise WeChatPublisherError(
                f"WeChat API error {data.get('errcode')}: {data.get('errmsg')}"
            )
        return data

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Fetch and cache the account access token."""
        if self._access_token and not force_refresh:
            return self._access_token

        session = self._get_session()
        response = session.get(
            TOKEN_URL,
            params={
                "grant_type": "client_credential",
                "appid": self.app_id,
                "secret": self.app_secret,
            },
            timeout=self.timeout,
        )
        data = self._parse_response(response)

        access_token = data.get("access_token")
        if not access_token:
            raise WeChatPublisherError("WeChat API did not return an access token.")

        self._access_token = access_token
        return access_token

    def upload_cover_image(self, image_path: str) -> Dict[str, Any]:
        """Upload a local cover image and return the permanent media info."""
        path = Path(image_path)
        if not path.exists():
            raise WeChatPublisherError(f"Cover image not found: {path}")

        access_token = self.get_access_token()
        session = self._get_session()
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

        with path.open("rb") as media_file:
            response = session.post(
                MATERIAL_ADD_URL,
                params={"access_token": access_token, "type": "image"},
                files={"media": (path.name, media_file, mime_type)},
                timeout=self.timeout,
            )

        return self._parse_response(response)

    def add_draft(self, article_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a draft article and return the raw API response."""
        access_token = self.get_access_token()
        session = self._get_session()
        response = session.post(
            DRAFT_ADD_URL,
            params={"access_token": access_token},
            json={"articles": [article_payload]},
            timeout=self.timeout,
        )
        return self._parse_response(response)

    def submit_publish(self, media_id: str) -> Dict[str, Any]:
        """Submit an existing draft for publishing."""
        access_token = self.get_access_token()
        session = self._get_session()
        response = session.post(
            FREEPUBLISH_SUBMIT_URL,
            params={"access_token": access_token},
            json={"media_id": media_id},
            timeout=self.timeout,
        )
        return self._parse_response(response)

    def get_publish_status(self, publish_id: str) -> Dict[str, Any]:
        """Query publish status for a previously submitted draft."""
        access_token = self.get_access_token()
        session = self._get_session()
        response = session.post(
            FREEPUBLISH_GET_URL,
            params={"access_token": access_token},
            json={"publish_id": publish_id},
            timeout=self.timeout,
        )
        return self._parse_response(response)


def resolve_wechat_credentials(args: argparse.Namespace) -> Tuple[str, str]:
    """Resolve WeChat AppID and AppSecret from CLI or environment."""
    app_id = first_non_empty(
        args.app_id,
        os.getenv("WECHAT_APP_ID"),
        os.getenv("WECHAT_OFFICIAL_ACCOUNT_APP_ID"),
        os.getenv("WEIXIN_APP_ID"),
    )
    app_secret = first_non_empty(
        args.app_secret,
        os.getenv("WECHAT_APP_SECRET"),
        os.getenv("WECHAT_OFFICIAL_ACCOUNT_APP_SECRET"),
        os.getenv("WEIXIN_APP_SECRET"),
    )

    if not app_id or not app_secret:
        raise WeChatPublisherError(
            "Missing WeChat credentials. Set WECHAT_APP_ID and WECHAT_APP_SECRET "
            "in the environment or pass --app-id/--app-secret."
        )

    return app_id, app_secret


def build_article_payload(
    title: str,
    body_text: str,
    body_html: str,
    author: Optional[str],
    digest: Optional[str],
    content_source_url: Optional[str],
    thumb_media_id: str,
    need_open_comment: int,
    only_fans_can_comment: int,
    show_cover_pic: int,
) -> Dict[str, Any]:
    """Build the article object expected by the draft API."""
    resolved_author = first_non_empty(author, default=DEFAULT_AUTHOR)
    resolved_digest = first_non_empty(digest, build_digest(body_text))

    return {
        "title": title,
        "author": resolved_author,
        "digest": resolved_digest,
        "content": body_html,
        "content_source_url": first_non_empty(content_source_url, default=""),
        "thumb_media_id": thumb_media_id,
        "need_open_comment": int(need_open_comment),
        "only_fans_can_comment": int(only_fans_can_comment),
        "show_cover_pic": int(show_cover_pic),
    }


def poll_publish_status(
    publisher: WeChatOfficialAccountPublisher,
    publish_id: str,
    timeout_seconds: int,
    interval_seconds: int,
) -> Dict[str, Any]:
    """Poll publish status for a limited time and return the last response."""
    deadline = time.time() + timeout_seconds
    last_response: Dict[str, Any] = {}

    while time.time() < deadline:
        last_response = publisher.get_publish_status(publish_id)
        publish_status = last_response.get("publish_status")

        if "article_id" in last_response or "article_detail" in last_response:
            break
        if publish_status not in (None, 0, 1):
            break

        time.sleep(max(1, interval_seconds))

    return last_response


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(
        description="Publish a local article file to a WeChat Official Account."
    )
    parser.add_argument(
        "article_path",
        nargs="?",
        help="Path to a UTF-8 article text file. The first non-empty line is used as the title.",
    )
    parser.add_argument("--env-file", default=".env", help="Optional .env file path.")
    parser.add_argument("--app-id", help="WeChat Official Account AppID.")
    parser.add_argument("--app-secret", help="WeChat Official Account AppSecret.")
    parser.add_argument("--title", help="Override the detected title.")
    parser.add_argument("--author", help="Article author name.")
    parser.add_argument("--digest", help="Article digest/summary shown in WeChat.")
    parser.add_argument(
        "--content-source-url",
        help="Optional original source URL shown in the article metadata.",
    )
    parser.add_argument(
        "--thumb-media-id",
        help="Existing permanent media_id for the article cover image.",
    )
    parser.add_argument(
        "--thumb-image",
        help="Local image path to upload as permanent material for the article cover.",
    )
    parser.add_argument(
        "--show-cover-pic",
        type=int,
        default=1,
        choices=(0, 1),
        help="Whether WeChat should show the cover image in the article body.",
    )
    parser.add_argument(
        "--need-open-comment",
        type=int,
        default=0,
        choices=(0, 1),
        help="Whether article comments are enabled.",
    )
    parser.add_argument(
        "--only-fans-can-comment",
        type=int,
        default=0,
        choices=(0, 1),
        help="Whether only followers can comment.",
    )
    parser.add_argument(
        "--draft-only",
        action="store_true",
        help="Create the draft but do not submit it for publishing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate HTML and payload preview only, without calling WeChat APIs.",
    )
    parser.add_argument(
        "--html-out",
        help="Optional file path to save the generated HTML preview.",
    )
    parser.add_argument(
        "--check-publish-id",
        help="Skip draft creation and query an existing publish_id instead.",
    )
    parser.add_argument(
        "--status-poll-seconds",
        type=int,
        default=0,
        help="If > 0, poll publish status for this many seconds after submit.",
    )
    parser.add_argument(
        "--status-poll-interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Seconds between publish status polls.",
    )
    return parser


def main() -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    load_env_file(args.env_file)

    try:
        if args.check_publish_id:
            app_id, app_secret = resolve_wechat_credentials(args)
            publisher = WeChatOfficialAccountPublisher(app_id=app_id, app_secret=app_secret)
            status = publisher.get_publish_status(args.check_publish_id)
            print(format_json(status))
            return 0

        if not args.article_path:
            parser.error("article_path is required unless --check-publish-id is used.")

        article = read_article_file(args.article_path, override_title=args.title)
        body_html = build_wechat_html(article.body_text)

        if args.html_out:
            save_text_file(args.html_out, body_html)

        thumb_media_id = first_non_empty(args.thumb_media_id, os.getenv("WECHAT_THUMB_MEDIA_ID"))
        if args.dry_run and not thumb_media_id:
            thumb_media_id = DRY_RUN_THUMB_MEDIA_ID

        payload = build_article_payload(
            title=article.title,
            body_text=article.body_text,
            body_html=body_html,
            author=first_non_empty(args.author, os.getenv("WECHAT_AUTHOR")),
            digest=first_non_empty(args.digest, os.getenv("WECHAT_DIGEST")),
            content_source_url=first_non_empty(
                args.content_source_url, os.getenv("WECHAT_CONTENT_SOURCE_URL")
            ),
            thumb_media_id=thumb_media_id or "",
            need_open_comment=args.need_open_comment,
            only_fans_can_comment=args.only_fans_can_comment,
            show_cover_pic=args.show_cover_pic,
        )

        if args.dry_run:
            print(format_json(payload))
            return 0

        app_id, app_secret = resolve_wechat_credentials(args)
        publisher = WeChatOfficialAccountPublisher(app_id=app_id, app_secret=app_secret)

        if not thumb_media_id and args.thumb_image:
            upload_result = publisher.upload_cover_image(args.thumb_image)
            thumb_media_id = upload_result.get("media_id")
            if not thumb_media_id:
                raise WeChatPublisherError(
                    f"Cover upload succeeded but media_id is missing: {format_json(upload_result)}"
                )
            payload["thumb_media_id"] = thumb_media_id

        if not payload["thumb_media_id"]:
            raise WeChatPublisherError(
                "A cover image is required. Pass --thumb-media-id, set WECHAT_THUMB_MEDIA_ID, "
                "or provide --thumb-image."
            )

        draft_result = publisher.add_draft(payload)
        print("Draft created:")
        print(format_json(draft_result))

        if args.draft_only:
            return 0

        media_id = draft_result.get("media_id")
        if not media_id:
            raise WeChatPublisherError(
                f"WeChat draft API response did not include media_id: {format_json(draft_result)}"
            )

        publish_result = publisher.submit_publish(media_id)
        print("Publish submitted:")
        print(format_json(publish_result))

        publish_id = publish_result.get("publish_id")
        if publish_id and args.status_poll_seconds > 0:
            final_status = poll_publish_status(
                publisher=publisher,
                publish_id=publish_id,
                timeout_seconds=args.status_poll_seconds,
                interval_seconds=args.status_poll_interval,
            )
            print("Latest publish status:")
            print(format_json(final_status))

        return 0

    except WeChatPublisherError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
