"""投稿キュー管理: JSONL形式で投稿待ちレコードを管理する。

使用例:
    queue.add_to_queue(record_id="uuid", article_file="/path/to/article.txt")
    pending = queue.get_queued()
    for record in pending:
        url = post_to_note(record['article_file'])
        queue.mark_posted(record['record_id'], url)
"""

import json
import os
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent


def _queue_file() -> Path:
    """投稿キューファイルパスを返す"""
    queue_dir = _ROOT / "out" / "approvals"
    queue_dir.mkdir(parents=True, exist_ok=True)
    return queue_dir / "posts_queue.jsonl"


def add_to_queue(record_id: str, article_file: str, tags: list = None) -> None:
    """投稿キューに新規レコードを追加する。

    Args:
        record_id: 承認レコード ID （Discord で生成された UUID）
        article_file: 記事ファイルパス
        tags: SEO ハッシュタグリスト（# なし）
    """
    fpath = _queue_file()
    record = {
        "record_id": record_id,
        "article_file": str(article_file),
        "tags": tags or [],
        "article_url": None,
        "status": "queued",
        "queued_at": datetime.now().isoformat(),
        "posted_at": None,
        "posted_url": None,
    }
    with open(fpath, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def get_queued() -> list[dict]:
    """status=queued の全レコードを返す"""
    fpath = _queue_file()
    if not fpath.exists():
        return []
    records = []
    with open(fpath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("status") == "queued":
                    records.append(rec)
            except json.JSONDecodeError:
                continue
    return records


def mark_posted(record_id: str, posted_url: str) -> bool:
    """レコードを投稿済みにマークする。

    Args:
        record_id: 承認レコード ID
        posted_url: 投稿後の記事 URL

    Returns:
        成功時 True、見つからない時 False
    """
    fpath = _queue_file()
    if not fpath.exists():
        return False

    lines = fpath.read_text(encoding="utf-8").splitlines()
    updated = False
    new_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            new_lines.append(line)
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            new_lines.append(line)
            continue

        if rec.get("record_id") == record_id:
            rec["status"] = "posted"
            rec["posted_at"] = datetime.now().isoformat()
            rec["posted_url"] = posted_url
            new_lines.append(json.dumps(rec, ensure_ascii=False))
            updated = True
        else:
            new_lines.append(line)

    if updated:
        fpath.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        return True

    return False


def load_all() -> list[dict]:
    """全レコード（queued + posted）を返す"""
    fpath = _queue_file()
    if not fpath.exists():
        return []
    records = []
    with open(fpath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records
