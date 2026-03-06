"""Discord通知モジュール: Threads投稿案をDiscordチャンネルに送信し承認待ちとして記録する。

Discord Bot Token方式 (REST API直接呼び出し) で実装。
ボタン付きメッセージの送信はBotトークンが必要なため、
承認ボタン付きメッセージを送信する。ボタン操作の受付は bot.py が担う。
"""

import hashlib
import json
import os
import uuid
import warnings
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

from automation.approve import store

# .env を明示パスで読み込み
_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env", override=False)

DISCORD_API_BASE = "https://discord.com/api/v10"


def _bot_token() -> str:
    return os.getenv("DISCORD_BOT_TOKEN", "")


def _channel_id() -> str:
    return os.getenv("DISCORD_CHANNEL_ID", "")


def _is_dry_run(dry_run: bool = False) -> bool:
    """--dry-run フラグまたは DISCORD_MODE=dry_run 環境変数で DRY RUN判定"""
    if dry_run:
        return True
    return os.getenv("DISCORD_MODE", "").lower() == "dry_run"


def _content_hash(content: str) -> str:
    """SHA256の先頭16文字をコンテンツハッシュとして返す"""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _extract_article_info(article_file: str) -> tuple[str, str]:
    """記事ファイルから（タイトル, 本文冒頭300文字）を抽出する。

    記事ファイルのフォーマット:
        ※本記事には広告が含まれます  ← 広告免責
        [実際のタイトル]              ← 2行目
        [導入文...]                   ← 3行目以降
    """
    if not article_file:
        return "", ""
    try:
        lines = Path(article_file).read_text(encoding="utf-8").splitlines()
    except Exception:
        return "", ""

    title = ""
    body_lines = []
    skip_disclaimer = True
    found_title = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if found_title:
                body_lines.append("")
            continue
        # 広告免責行をスキップ
        if skip_disclaimer and "広告" in stripped:
            skip_disclaimer = False
            continue
        # タイトル（広告免責の次の非空行）
        if not found_title:
            title = stripped
            found_title = True
            continue
        # 本文
        body_lines.append(stripped)

    preview = "\n".join(body_lines)[:300]
    return title, preview


def _build_message_payload(
    content: str,
    source_file: str,
    record_id: str,
    index: int = 1,
    article_title: str = "",
    article_preview: str = "",
    tags: list = None,
) -> dict:
    """Discord APIに送るメッセージペイロードを組み立てる。

    ボタン付きEmbedメッセージ形式。
    記事タイトル・本文プレビュー・Threads案・ハッシュタグを分けて表示する。
    """
    tags = tags or []
    tags_str = "  ".join(f"#{t}" for t in tags) if tags else "（なし）"

    # 記事タイトルセクション
    title_section = f"**📌 記事タイトル**\n{article_title}" if article_title else ""
    # 本文プレビューセクション
    preview_section = (
        f"**📄 本文冒頭（300文字）**\n{article_preview}..."
        if article_preview else ""
    )
    # ハッシュタグセクション
    hashtag_section = f"**🏷️ ハッシュタグ（SEO）**\n{tags_str}"

    description_parts = []
    if title_section:
        description_parts.append(title_section)
    if preview_section:
        description_parts.append(preview_section)
    description_parts.append(
        "──── Threads投稿案 ────\n"
        f"{content}\n"
        "──────────────────────"
    )
    description_parts.append(hashtag_section)
    description_parts.append(f"ID: `{record_id}`")

    embed = {
        "title": f"📝 note記事案 #{index:03d}",
        "description": "\n\n".join(description_parts),
        "color": 0x5865F2,  # Discord Blurple
        "timestamp": datetime.utcnow().isoformat(),
    }

    components = [
        {
            "type": 1,  # ACTION_ROW
            "components": [
                {
                    "type": 2,  # BUTTON
                    "style": 3,  # SUCCESS (green)
                    "label": "✅ 承認",
                    "custom_id": f"approve:{record_id}",
                },
                {
                    "type": 2,  # BUTTON
                    "style": 4,  # DANGER (red)
                    "label": "❌ 却下",
                    "custom_id": f"reject:{record_id}",
                },
            ],
        }
    ]

    return {"embeds": [embed], "components": components}


def _send_discord_message(payload: dict) -> dict | None:
    """Discord REST APIにメッセージを送信し、レスポンスのdictを返す。失敗時はNone。"""
    token = _bot_token()
    channel = _channel_id()

    if not token or not channel:
        warnings.warn(
            "[Discord] DISCORD_BOT_TOKEN または DISCORD_CHANNEL_ID が未設定です。通知をスキップします。"
        )
        return None

    url = f"{DISCORD_API_BASE}/channels/{channel}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        warnings.warn(f"[Discord] メッセージ送信失敗: {e}")
        return None


def send_for_approval(
    content: str,
    source_file: str = "",
    article_file: str = "",
    tags: list = None,
    kind: str | None = None,
    index: int = 1,
    dry_run: bool = False,
) -> dict | None:
    """Threads投稿案をDiscordに送信し、承認待ちレコードとして記録する。

    Args:
        content: 投稿本文（Threads テキスト）
        source_file: ソースファイルパス（ログ用）
        article_file: 対応する記事ファイルパス（Note投稿用）
        tags: SEO ハッシュタグリスト（# なし）
        kind: 承認種別（デフォルト: 環境変数 APPROVAL_KIND_THREADS or "threads"）
        index: 投稿連番（表示用）
        dry_run: True の場合は送信せずプレビューをstdoutに表示

    Returns:
        作成した承認レコード dict、または送信スキップ時は None
    """
    tags = tags or []
    if kind is None:
        kind = os.getenv("APPROVAL_KIND_THREADS", "threads")

    content_hash = _content_hash(content)

    # 記事ファイルから タイトル・本文プレビューを抽出
    article_title, article_preview = _extract_article_info(article_file)

    # 幂等性チェック: 同一ハッシュが pending/approved なら送信しない
    existing = store.find_by_hash(content_hash)
    if existing is not None:
        status = existing.get("status", "unknown")
        print(f"  [SKIP] 既存レコードあり (status={status}, hash={content_hash})")
        return None

    record_id = str(uuid.uuid4())

    if _is_dry_run(dry_run):
        # DRY RUN: コンソールにプレビュー出力
        print("\n" + "=" * 50)
        print(f"  [DRY RUN] Discord通知プレビュー")
        print(f"  ソース: {Path(source_file).name if source_file else '不明'}")
        print(f"  記事タイトル: {article_title or '（なし）'}")
        print(f"  タグ: {', '.join(tags) or '（なし）'}")
        print(f"  ID:     {record_id}")
        print(f"  Hash:   {content_hash}")
        print("-" * 50)
        print(content)
        print("=" * 50)
        print(f"  [DRY RUN] ボタン: [✅ 承認] [❌ 却下]")
        return None

    # メッセージペイロード組み立て
    payload = _build_message_payload(
        content, source_file, record_id,
        index=index,
        article_title=article_title,
        article_preview=article_preview,
        tags=tags,
    )

    # Discord送信
    resp = _send_discord_message(payload)

    discord_message_id = str(resp["id"]) if resp and "id" in resp else None
    channel = _channel_id()

    # 承認レコード作成
    record = {
        "id": record_id,
        "type": kind,
        "status": "pending",
        "source_file": str(source_file),
        "article_file": str(article_file) if article_file else None,
        "tags": tags,
        "content_hash": content_hash,
        "content_preview": content[:50].replace("\n", " "),
        "created_at": datetime.now().isoformat(),
        "decided_at": None,
        "decided_by": None,
        "discord_message_id": discord_message_id,
        "channel_id": channel,
    }
    store.append_record(record)

    if discord_message_id:
        print(f"  [Discord] 送信完了: message_id={discord_message_id}, record_id={record_id}")
    else:
        print(f"  [Discord] 送信失敗（ログのみ記録）: record_id={record_id}")

    return record
