"""
AI記事工場 メインオーケストレーター

Usage:
    python run_auto.py                  # 全ステップ実行
    python run_auto.py --trends-only    # トレンド収集のみ
    python run_auto.py --articles-only  # 記事生成のみ（既存トレンド使用）
    python run_auto.py --count 5        # 5記事生成
    python run_auto.py --dry-run        # API呼び出しなし（テスト用）
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from automation.common.config_loader import load_config
from automation.common.claude_client import ClaudeClient, DryRunClient
from automation.trends.collector import collect_trends
from automation.articles.generator import generate_articles
from automation.affiliate.optimizer import generate_affiliate_suggestions
from automation.premium.generator import generate_premium_plan
from automation.threads.generator import generate_threads_post
from automation.quality.inspector import inspect_and_save


def print_banner():
    print("=" * 60)
    print("  AI記事工場 - note自動化パイプライン")
    print(f"  実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


def run_pipeline(args):
    print_banner()

    # 設定読み込み
    print("\n[0/6] 設定読み込み...")
    cfg = load_config()

    if args.dry_run:
        print("  *** DRY RUN モード: API呼び出しは行いません ***")
        fast_client = DryRunClient()
        article_client = DryRunClient()
    else:
        if not cfg.anthropic_api_key:
            print("エラー: ANTHROPIC_API_KEY が設定されていません")
            print("  .env ファイルに ANTHROPIC_API_KEY=sk-ant-xxxxx を設定してください")
            sys.exit(1)
        fast_client = ClaudeClient(cfg.anthropic_api_key, model_kind="FAST")

        article_client = ClaudeClient(cfg.anthropic_api_key, model_kind="ARTICLE")

    out = cfg.out_dir
    trends_dir = str(out / "trends")
    articles_dir = str(out / "articles")
    affiliate_dir = str(out / "affiliate")
    premium_dir = str(out / "premium")
    threads_dir = str(out / "threads")
    reports_dir = str(out / "reports")

    # ① SEOトレンド収集
    if not args.articles_only:
        print("\n[1/6] SEOトレンド収集...")
        trends = collect_trends(fast_client, cfg.topics["genres"], trends_dir)
        print(f"  完了: {len(trends.get('keywords', []))}キーワード")
    else:
        print("\n[1/6] SEOトレンド収集... スキップ (--articles-only)")

    # ② 記事生成
    if not args.trends_only:
        print(f"\n[2/6] 記事生成 ({args.count}本)...")
        article_results = generate_articles(article_client, trends_dir, articles_dir, count=args.count)
        print(f"  完了: {len(article_results)}本生成")
    else:
        print("\n[2/6] 記事生成... スキップ (--trends-only)")
        article_results = []

    # ③〜⑥: 記事ごとに後続処理
    if article_results and not args.trends_only:
        # ③ アフィリエイト候補
        print(f"\n[3/6] アフィリエイト候補生成...")
        for r in article_results:
            print(f"  [{r['index']}] {r['keyword']}")
            generate_affiliate_suggestions(
                fast_client,
                r["keyword"],
                r["genre"],
                cfg.affiliate["categories"],
                affiliate_dir,
                index=r["index"],
            )
        print("  完了")

        # ④ 有料note企画
        print(f"\n[4/6] 有料note企画生成...")
        for r in article_results:
            print(f"  [{r['index']}] {r['keyword']}")
            generate_premium_plan(
                fast_client,
                r["keyword"],
                r["genre"],
                r["char_count"],
                premium_dir,
                index=r["index"],
            )
        print("  完了")

        # ⑤ Threads投稿
        print(f"\n[5/6] Threads投稿生成...")
        for r in article_results:
            print(f"  [{r['index']}] {r['keyword']}")
            generate_threads_post(
                fast_client,
                r["keyword"],
                r["genre"],
                threads_dir,
                index=r["index"],
            )
        print("  完了")

        # ⑥ 自動検査
        print(f"\n[6/6] 記事検査...")
        all_pass = True
        for r in article_results:
            print(f"  [{r['index']}] {r['keyword']}")
            report = inspect_and_save(r["file"], reports_dir)
            status = report["overall"]
            if status != "pass":
                all_pass = False
                fails = [
                    k for k, v in report["checks"].items()
                    if v["status"] != "pass"
                ]
                print(f"    ❌ FAIL: {', '.join(fails)}")
            else:
                print(f"    ✅ PASS")
        print(f"  検査完了: {'全件PASS' if all_pass else '一部FAIL あり'}")
    else:
        print("\n[3/6] アフィリエイト候補... スキップ")
        print("[4/6] 有料note企画... スキップ")
        print("[5/6] Threads投稿... スキップ")
        print("[6/6] 記事検査... スキップ")

    # サマリー
    print("\n" + "=" * 60)
    print("  実行完了サマリー")
    print("=" * 60)
    print(f"  トレンド:     {trends_dir}")
    print(f"  記事:         {articles_dir}")
    print(f"  広告候補:     {affiliate_dir}")
    print(f"  有料note:     {premium_dir}")
    print(f"  Threads:      {threads_dir}")
    print(f"  検査レポート: {reports_dir}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="AI記事工場 - note自動化パイプライン")
    parser.add_argument("--trends-only", action="store_true", help="トレンド収集のみ実行")
    parser.add_argument("--articles-only", action="store_true", help="記事生成のみ実行（既存トレンド使用）")
    parser.add_argument("--count", type=int, default=3, help="生成記事数（デフォルト: 3）")
    parser.add_argument("--dry-run", action="store_true", help="API呼び出しなし（テスト用）")
    args = parser.parse_args()

    if args.trends_only and args.articles_only:
        print("エラー: --trends-only と --articles-only は同時に指定できません")
        sys.exit(1)

    run_pipeline(args)


if __name__ == "__main__":
    main()
