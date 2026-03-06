"""CLI: 投稿キューから記事をnoteに投稿し、Threads文言を生成・提供する。

使用方法:
    python tools/post_and_generate_threads.py --process-queue [--dry-run]
    python tools/post_and_generate_threads.py --list-queue
"""

import argparse
import sys
from pathlib import Path

# プロジェクトルートをPATHに追加
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env", override=False)

from automation.poster.note_client import create_note_client
from automation.poster.queue import get_queued, mark_posted, load_all
from automation.poster.threads_formatter import generate_threads_text


def extract_article_title(article_file: str) -> str:
    """記事ファイルから実際のタイトルを抽出する。

    記事フォーマット:
        ※本記事には広告が含まれます  ← 広告免責（スキップ）
        [実際のタイトル]              ← ここを抽出
        [導入文...]
    """
    try:
        lines = Path(article_file).read_text(encoding="utf-8").splitlines()
    except Exception:
        return ""

    skip_disclaimer = True
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if skip_disclaimer and "広告" in stripped:
            skip_disclaimer = False
            continue
        if stripped:
            return stripped  # 広告免責の次の非空行 = タイトル
    return Path(article_file).stem  # フォールバック: ファイル名


def load_article_metadata(article_file: str) -> dict:
    """記事ファイルからメタデータを抽出する。

    Args:
        article_file: 記事ファイルパス（例: `2026-03-05_001_AI副業_始め方.txt`）

    Returns:
        {title, genre, keyword, ...} を含む dict
    """
    fpath = Path(article_file)
    if not fpath.exists():
        return {"keyword": "記事", "genre": "", "title": ""}

    # ファイル名からメタデータを抽出（例: 2026-03-05_001_AI副業_始め方.txt）
    # → keyword = "AI副業_始め方", genre = "AI副業"
    name = fpath.stem  # 拡張子なし
    parts = name.split("_", 2)  # 日付_index_キーワード...
    if len(parts) >= 3:
        keyword = parts[2]
        # genre を推測（キーワードに含まれるジャンル）
        genre = ""
        for g in ["AI副業", "AIツール", "IT初心者", "Linux", "Docker", "自宅サーバー"]:
            if g in keyword:
                genre = g
                break
    else:
        keyword = name
        genre = ""

    # 記事ファイル内の実タイトルを抽出（Claude が生成したタイトル）
    actual_title = extract_article_title(article_file) or keyword

    return {
        "keyword": keyword,
        "genre": genre,
        "title": actual_title,  # ✅ Claude 生成の実タイトル（キーワードではなく）
    }


def process_queue(dry_run: bool = False) -> None:
    """投稿キューから記事をnoteに投稿する。

    Args:
        dry_run: True ならシミュレーションモード
    """
    print("\n" + "=" * 60)
    print("  Note投稿・Threads文言生成")
    print("=" * 60)

    # キューから投稿待ちレコードを取得
    pending = get_queued()
    print(f"\n投稿待ち: {len(pending)} 件")

    if not pending:
        print("キューに投稿待ちレコードがありません")
        return

    # Note クライアント初期化
    note_client = create_note_client(dry_run=dry_run)
    if not dry_run:
        if not note_client.login():
            print("❌ Note ログイン失敗。終了します")
            return

    # 投稿処理
    posted_urls = {}
    for i, record in enumerate(pending, 1):
        record_id = record.get("record_id")
        article_file = record.get("article_file")

        print(f"\n[{i}/{len(pending)}] 投稿処理中...")
        print(f"  ファイル: {article_file}")

        # 記事ファイルを読み込む
        try:
            content = Path(article_file).read_text(encoding="utf-8")
        except Exception as e:
            print(f"  ❌ ファイル読込失敗: {e}")
            continue

        # メタデータを抽出
        metadata = load_article_metadata(article_file)
        title = metadata["title"]
        keyword = metadata["keyword"]
        genre = metadata["genre"]

        # タグを取得（queue レコードに tags フィールドがあれば使用）
        tags = record.get("tags", [])

        print(f"  タイトル: {title}")
        print(f"  ジャンル: {genre}")
        print(f"  タグ: {', '.join(tags) if tags else '（なし）'}")

        # Note に投稿
        article_url = note_client.post_article(title=title, content=content, tags=tags)
        if not article_url:
            print(f"  ❌ 投稿失敗")
            continue

        print(f"  ✅ 投稿成功")
        print(f"  URL: {article_url}")

        # キューを更新
        if not dry_run:
            mark_posted(record_id, article_url)

        posted_urls[keyword] = {
            "url": article_url,
            "genre": genre,
            "metadata": metadata,
        }

    note_client.close()

    # Threads 文言を生成・表示
    print("\n" + "=" * 60)
    print("  Threads投稿文言（コピペ用）")
    print("=" * 60)

    for keyword, data in posted_urls.items():
        url = data["url"]
        genre = data["genre"]

        threads_text = generate_threads_text(
            keyword=keyword,
            article_url=url,
            genre=genre,
        )

        print(f"\n【{keyword}】")
        print("-" * 60)
        print(threads_text)
        print("-" * 60)

    print(f"\n✅ 投稿完了: {len(posted_urls)} 件")


def list_queue() -> None:
    """キューの内容を表示する。"""
    print("\n" + "=" * 60)
    print("  投稿キュー内容")
    print("=" * 60)

    all_records = load_all()
    if not all_records:
        print("キューが空です")
        return

    # ステータスごとに分類
    queued = [r for r in all_records if r.get("status") == "queued"]
    posted = [r for r in all_records if r.get("status") == "posted"]

    print(f"\n投稿待ち (queued): {len(queued)} 件")
    for r in queued:
        print(f"  - {r.get('record_id')[:8]}... ({Path(r.get('article_file', '')).name})")

    print(f"\n投稿済み (posted): {len(posted)} 件")
    for r in posted:
        url = r.get("posted_url", "")
        print(f"  - {r.get('record_id')[:8]}... → {url}")


def main():
    parser = argparse.ArgumentParser(description="Note投稿・Threads文言生成ツール")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--process-queue",
        action="store_true",
        help="投稿キューから記事をNote に投稿し、Threads文言を生成",
    )
    group.add_argument(
        "--list-queue",
        action="store_true",
        help="投稿キューの内容を表示",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="シミュレーションモード（実際には投稿しない）",
    )
    args = parser.parse_args()

    if args.process_queue:
        process_queue(dry_run=args.dry_run)
    elif args.list_queue:
        list_queue()


if __name__ == "__main__":
    main()
