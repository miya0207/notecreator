"""CLI: Threads投稿案をDiscordに送信して承認待ち状態にする。

使用方法:
    python tools/send_threads_for_approval.py --latest        # 最新日付の全ファイルを送信
    python tools/send_threads_for_approval.py --all           # out/threads/ の全ファイルを送信
    python tools/send_threads_for_approval.py --file PATH     # 指定ファイルを送信
    python tools/send_threads_for_approval.py --latest --dry-run  # 送信せずプレビュー

同一コンテンツ（SHA256ハッシュで判定）は重複送信しない。
"""

import argparse
import sys
from pathlib import Path

# プロジェクトルートをPATHに追加（tools/ から実行されるため）
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env", override=False)

from automation.notify.discord_notifier import send_for_approval
from automation.approve import store as approval_store


def _collect_latest(threads_dir: Path) -> list[Path]:
    """threads_dir の中で最新日付のファイル群を返す"""
    if not threads_dir.exists():
        print(f"エラー: {threads_dir} が存在しません")
        return []
    all_files = sorted(threads_dir.glob("*.txt"), reverse=True)
    if not all_files:
        print(f"  {threads_dir} にファイルがありません")
        return []
    # ファイル名先頭の日付部分（YYYY-MM-DD）でグルーピング
    latest_date = all_files[0].name[:10]
    return [f for f in all_files if f.name.startswith(latest_date)]


def _collect_all(threads_dir: Path) -> list[Path]:
    """threads_dir の全 .txt ファイルを返す（日付降順）"""
    if not threads_dir.exists():
        print(f"エラー: {threads_dir} が存在しません")
        return []
    return sorted(threads_dir.glob("*.txt"), reverse=True)


def _send_file(fpath: Path, index: int, dry_run: bool) -> bool:
    """1ファイルを送信する。送信成功/スキップで True、エラーで False を返す"""
    if not fpath.exists():
        print(f"  エラー: {fpath} が存在しません")
        return False

    content = fpath.read_text(encoding="utf-8").strip()
    if not content:
        print(f"  [SKIP] 空ファイル: {fpath.name}")
        return True

    print(f"\n  [{index}] {fpath.name}")
    result = send_for_approval(
        content=content,
        source_file=str(fpath),
        index=index,
        dry_run=dry_run,
    )
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Threads投稿案をDiscordに送信して承認待ち状態にする"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--latest", action="store_true", help="最新日付のファイル群を送信")
    group.add_argument("--all", action="store_true", help="out/threads/ の全ファイルを送信")
    group.add_argument("--file", metavar="PATH", help="指定ファイルを送信")
    parser.add_argument("--dry-run", action="store_true", help="送信せずプレビューを出力")
    args = parser.parse_args()

    threads_dir = _ROOT / "out" / "threads"

    if args.file:
        files = [Path(args.file)]
    elif args.latest:
        files = _collect_latest(threads_dir)
    else:  # --all
        files = _collect_all(threads_dir)

    if not files:
        print("送信するファイルがありません。")
        sys.exit(0)

    mode_label = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{mode_label}Threads投稿案をDiscordに送信します")
    print(f"  対象ファイル: {len(files)} 件")
    print(f"  threads_dir: {threads_dir}")

    # 送信前サマリー
    if args.dry_run:
        print("  *** DRY RUN: 実際には送信しません ***")

    success = 0
    for i, fpath in enumerate(files, 1):
        _send_file(fpath, index=i, dry_run=args.dry_run)
        success += 1

    print(f"\n完了: {success}/{len(files)} 件処理")

    # pending 状態の確認
    if not args.dry_run:
        pending = approval_store.load_pending()
        print(f"  現在の承認待ち: {len(pending)} 件")


if __name__ == "__main__":
    main()
