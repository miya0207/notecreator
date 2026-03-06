"""承認ログ管理: JSONL形式で承認/却下履歴を保存・検索する"""

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

# デフォルト出力先（環境変数で上書き可）
_ROOT = Path(__file__).resolve().parent.parent.parent


def _log_dir() -> Path:
    """環境変数 APPROVAL_LOG_DIR からログディレクトリを取得する。
    パストラバーサル対策: _ROOT 配下のパスのみ許可する。
    """
    raw = os.getenv("APPROVAL_LOG_DIR", "")
    if raw:
        p = Path(raw)
        # 相対パスは _ROOT からの相対として解決
        resolved = (p if p.is_absolute() else _ROOT / p).resolve()
        # _ROOT 配下のパスのみ許可（パストラバーサル防止）
        try:
            resolved.relative_to(_ROOT.resolve())
            return resolved
        except ValueError:
            raise ValueError(
                f"APPROVAL_LOG_DIR '{raw}' はプロジェクト外のパスです。"
                f"プロジェクトルート ({_ROOT}) 配下のパスのみ許可されます。"
            )
    return _ROOT / "out" / "approvals"


def _today_file() -> Path:
    """当日の承認ログファイルパスを返す"""
    d = _log_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / f"approvals_{date.today().isoformat()}.jsonl"


def _iter_recent_records(days: int = 7):
    """直近 days 日分の全レコードをイテレートする"""
    log_dir = _log_dir()
    if not log_dir.exists():
        return
    today = date.today()
    for i in range(days):
        target = today - timedelta(days=i)
        fpath = log_dir / f"approvals_{target.isoformat()}.jsonl"
        if not fpath.exists():
            continue
        with open(fpath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line), fpath
                except json.JSONDecodeError:
                    continue


def find_by_hash(content_hash: str) -> dict | None:
    """content_hash が一致するレコードを直近7日から検索して返す。なければ None。"""
    for record, _ in _iter_recent_records():
        if record.get("content_hash") == content_hash:
            return record
    return None


def find_by_id(record_id: str) -> dict | None:
    """record_id が一致するレコードを直近7日から検索して返す。なければ None。"""
    for record, _ in _iter_recent_records():
        if record.get("id") == record_id:
            return record
    return None


def append_record(record: dict) -> None:
    """新規レコードを当日のJSONLファイルに追記する

    レコード例:
        {
            "id": "uuid4",
            "type": "threads",
            "status": "pending",
            "source_file": "...",
            "article_file": "/path/to/article.txt",  # ← Note投稿用（追加）
            "content_hash": "...",
            "content_preview": "...",
            "created_at": "ISO8601",
            "decided_at": null,
            "decided_by": null,
            "discord_message_id": "...",
            "channel_id": "..."
        }
    """
    fpath = _today_file()
    with open(fpath, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def update_status(
    record_id: str,
    status: str,
    decided_by: str,
    decided_at: str | None = None,
) -> bool:
    """record_id に一致するレコードのステータスを更新する。

    当日ファイル → 昨日ファイル の順で検索し、最初に見つかったファイルを更新する。
    更新できたら True、見つからなければ False を返す。
    """
    if decided_at is None:
        decided_at = datetime.now().isoformat()

    for _, fpath in _iter_recent_records():
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
            if rec.get("id") == record_id:
                rec["status"] = status
                rec["decided_by"] = decided_by
                rec["decided_at"] = decided_at
                new_lines.append(json.dumps(rec, ensure_ascii=False))
                updated = True
            else:
                new_lines.append(line)

        if updated:
            fpath.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            return True

    return False


def load_pending() -> list[dict]:
    """status=pending の全レコードを直近7日から収集して返す"""
    results = []
    for record, _ in _iter_recent_records():
        if record.get("status") == "pending":
            results.append(record)
    return results


def load_today() -> list[dict]:
    """当日ファイルの全レコードを返す"""
    fpath = _today_file()
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
