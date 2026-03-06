"""Anthropic Claude API ラッパー（リトライ＋レート制限対応）"""

import json
import os
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# .env を明示パスで読み込み（作業ディレクトリに依存しない）
_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env", override=False)

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0


def _model_from_env(kind: str | None = None) -> str:
    """環境変数からモデル名を取得。kind='ARTICLE'/'FAST'/None"""
    if kind:
        v = os.getenv(f"CLAUDE_MODEL_{kind}")
        if v:
            return v
    return os.getenv("CLAUDE_MODEL", DEFAULT_MODEL)


class ClaudeClient:
    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        model_kind: str | None = None,
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model or _model_from_env(model_kind)
        print(f"  ClaudeClient: model={self.model}")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
    ) -> str:
        """Claude APIでテキスト生成（リトライ付き）"""
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return response.content[0].text
            except anthropic.RateLimitError:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"  レート制限: {delay}秒待機 (試行 {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
            except anthropic.NotFoundError:
                print(f"\n[エラー] モデル '{self.model}' が見つかりません。")
                print("  .env を確認してください:")
                print("    CLAUDE_MODEL_ARTICLE=claude-sonnet-4-6")
                print("    CLAUDE_MODEL_FAST=claude-haiku-4-5-20251001")
                print("    CLAUDE_MODEL=claude-sonnet-4-6")
                raise
            except anthropic.APIError as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"  APIエラー: {e} - {delay}秒後リトライ (試行 {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
        raise RuntimeError("Claude API: 最大リトライ回数超過")

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
    ) -> dict:
        """Claude APIでJSON生成（パース付き）"""
        text = self.generate(system_prompt, user_prompt, max_tokens)
        text = text.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]
        return json.loads(text.strip())


# ---------------------------------------------------------------------------
# DRY RUN用テンプレート
# 注意: str.replace() で {keyword} のみ置換するため、
#       {{A8_LINK_TOP}} は二重ブレースのまま保持される。
#       f-string / .format() は使わないこと。
# ---------------------------------------------------------------------------
_DRY_RUN_ARTICLE = (
    "※本記事には広告が含まれます\n\n"
    "{keyword}の完全入門ガイド\n\n"
    "近年、{keyword}への関心が急速に高まっています。"
    "特にIT初心者の方からも「試してみたい」という声が増えており、"
    "本記事では初心者の方でも理解しやすいよう、基礎から丁寧に解説します。"
    "この記事を読むことで、{keyword}の全体像が把握でき、"
    "最初の一歩を踏み出す準備が整います。\n\n"
    "■ この記事でわかること\n\n"
    "・{keyword}の基本概念と仕組みがわかる\n"
    "・具体的にどう活用できるかがわかる\n"
    "・初心者が最初に取り組むべきことがわかる\n"
    "・無料で試せるツールの使い方がわかる\n"
    "・次のステップへの進め方がわかる\n\n"
    "[DRY RUN] {keyword}とは、端的に言えば「誰でも使えるようになった最先端技術」です。"
    "数年前まで専門家だけが扱っていたものが、今では無料で試せるツールとして"
    "一般公開されています。初心者がつまずきがちなのは「難しそう」という先入観ですが、"
    "実際にはスマートフォンのアプリを使う感覚で始められるものがほとんどです。\n\n"
    "[DRY RUN] まずは「試してみる」という姿勢が大切です。"
    "本文セクション1: このテキストはDRY RUNモードで生成されたダミーコンテンツです。"
    "実際のAPI実行時には、Claude APIが1200文字以上の詳細な記事を生成します。\n\n"
    "[DRY RUN] {keyword}を始めるにあたって、多くの初心者が最初にぶつかる壁は"
    "「どこから手をつければいいかわからない」という点です。"
    "しかし心配はいりません。この記事で紹介する手順に沿って進めれば、"
    "誰でも最初の一歩を踏み出すことができます。\n\n"
    "【おすすめツール】\n"
    "{{A8_LINK_TOP}}\n\n"
    "[DRY RUN] 実際に{keyword}を活用するためのステップを見ていきましょう。"
    "ステップ1は無料ツールへの登録です。"
    "ステップ2では基本機能を試します。"
    "ステップ3で自分のユースケースに応用していきます。"
    "小さく始めて、成功体験を積み重ねることが大切です。\n\n"
    "[DRY RUN] 本文セクション2: 実際の運用では、具体的な手順や詳細な説明がここに入ります。"
    "たとえば、{keyword}に関連するツールやサービスの比較、"
    "実際の使い方のステップバイステップ解説、"
    "よくある失敗例とその対処法などが含まれます。\n\n"
    "【おすすめサービス】\n"
    "{{A8_LINK_MID}}\n\n"
    "[DRY RUN] まとめ: {keyword}は難しくありません。"
    "本記事で解説した通り、初心者でも十分に取り組める分野です。"
    "大切なのは「完璧を目指さず、まず試す」こと。"
    "小さな成功体験を積み重ねることで、自然とスキルが身についていきます。"
    "今日から第一歩を踏み出しましょう。"
    "まずは無料ツールに登録して、5分間だけ触ってみてください。"
    "それだけで世界が変わります。\n\n"
    "【おすすめ】\n"
    "{{A8_LINK_BOTTOM}}\n"
)

_DRY_RUN_KEYWORDS = [
    {
        "keyword": "AI副業 始め方",
        "genre": "AI副業",
        "search_demand": 8,
        "competition": 5,
        "beginner_demand": 9,
        "score": 14.4,
        "reason": "[DRY RUN] AI副業への関心が高い",
    },
    {
        "keyword": "ChatGPT 活用術",
        "genre": "AIツール",
        "search_demand": 7,
        "competition": 6,
        "beginner_demand": 8,
        "score": 9.3,
        "reason": "[DRY RUN] ChatGPT利用者が増加中",
    },
    {
        "keyword": "Docker 初心者 入門",
        "genre": "Docker",
        "search_demand": 6,
        "competition": 4,
        "beginner_demand": 7,
        "score": 10.5,
        "reason": "[DRY RUN] Docker需要が増加傾向",
    },
]


class DryRunClient:
    """API呼び出しなしのモッククライアント（テスト用）。
    検査PASSできる構造（1200文字以上・必須セクション全て）を返す。
    """

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
        """検査PASSできる最低限の構造を持つダミー記事を返す"""
        keyword = "AIツール"
        if "キーワード:" in user_prompt:
            keyword = user_prompt.split("キーワード:")[1].split("\n")[0].strip()
        # str.replace() で {keyword} のみ置換（{{A8_LINK_*}} は変換しない）
        return _DRY_RUN_ARTICLE.replace("{keyword}", keyword)

    def generate_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> dict:
        """collect_trends / affiliate / premium の各キーを含むダミーJSONを返す"""
        return {
            "dry_run": True,
            # collect_trends 用
            "keywords": _DRY_RUN_KEYWORDS,
            # generate_affiliate_suggestions 用
            "keyword": "[DRY RUN]",
            "genre": "AIツール",
            "recommendations": [
                {
                    "category": "AIツール",
                    "a8_search_keywords": ["AI ツール", "ChatGPT Plus", "AI サービス"],
                    "recommended_services": ["ChatGPT", "Claude"],
                    "appeal_points": "[DRY RUN] テスト用",
                    "placement": "TOP",
                }
            ],
            # generate_premium_plan 用
            "premium_note": {
                "title": "[DRY RUN] 有料noteタイトル",
                "subtitle": "テスト用サブタイトル",
                "target_reader": "IT初心者",
                "toc": ["第1章: 概要", "第2章: 実践", "第3章: 応用"],
                "estimated_pages": 15,
                "price_recommendation": {"price": 980, "reason": "[DRY RUN]"},
                "price_options": [980, 1980, 2980],
                "upsell_text": "[DRY RUN] さらに詳しい内容は有料noteで解説しています。",
            },
        }
