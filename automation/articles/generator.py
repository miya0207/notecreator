"""AI記事工場: SEOトレンドを元にClaude APIで記事を生成"""

import json
from datetime import date
from pathlib import Path

from automation.articles.formatter import ensure_article_structure, format_raw_article
from automation.common.claude_client import ClaudeClient

SYSTEM_PROMPT = """\
あなたは「AI × IT初心者」ジャンルのnote記事ライターです。

ルール:
- 1200文字以上の記事を書いてください
- 対象読者はIT初心者です。専門用語には必ず簡単な説明を添えてください
- 誇大広告は禁止です（「絶対稼げる」「確実に」「100%」などは使わないでください）
- 記事はプレーンテキストで出力してください（Markdown記号 #, *, `, > や HTMLタグは一切使わないでください）
- 広告プレースホルダー {{A8_LINK_TOP}}, {{A8_LINK_MID}}, {{A8_LINK_BOTTOM}} は必ずそのまま残してください
- 読みやすく、初心者が「自分にもできそう」と感じる文体で書いてください
"""

ARTICLE_TEMPLATE = """\
以下のキーワードとジャンルでnote記事を1本書いてください。

キーワード: {keyword}
ジャンル: {genre}

以下のフォーマットに厳密に従ってください。各セクションを省略せず必ず出力してください:

※本記事には広告が含まれます

[記事タイトル（キーワードを含む、30文字以内）]

[導入文: このテーマがなぜ注目されているか、読者の悩みに共感する内容。3〜5文]

■ この記事でわかること

[箇条書きで3〜5項目。各項目は「・」で始めてください]

[本文セクション1: テーマの基礎知識や概要を解説。初心者にわかりやすく。500文字以上]

【おすすめツール】
{{{{A8_LINK_TOP}}}}

[本文セクション2: 具体的な方法やステップを解説。400文字以上]

【おすすめサービス】
{{{{A8_LINK_MID}}}}

[まとめ: 読者への応援メッセージと次のアクション。200文字以上]

【おすすめ】
{{{{A8_LINK_BOTTOM}}}}
"""

MIN_CHAR_COUNT = 1200

HASHTAG_PROMPT = """\
以下のnote記事に最適なハッシュタグを3〜5個提案してください。
- #は付けない（例: AI副業）
- カンマ区切りで1行にまとめる
- SEO効果が高く、note.comで実際に使われるタグを選ぶ

キーワード: {keyword}
ジャンル: {genre}
"""


def generate_hashtags(client: "ClaudeClient", keyword: str, genre: str) -> list[str]:
    """キーワード・ジャンルから SEO 用ハッシュタグリストを生成して返す。

    Args:
        client: Claude API クライアント
        keyword: SEO キーワード
        genre: 記事ジャンル

    Returns:
        ハッシュタグリスト（# なし）。最大5個。
    """
    prompt = HASHTAG_PROMPT.format(keyword=keyword, genre=genre)
    try:
        raw = client.generate("", prompt, max_tokens=100)
        # "AI副業, ChatGPT, 副業初心者" → ["AI副業", "ChatGPT", "副業初心者"]
        tags = [t.strip().lstrip("#") for t in raw.split(",")]
        tags = [t for t in tags if t and len(t) <= 20]
        return tags[:5]
    except Exception as e:
        print(f"    ⚠️ ハッシュタグ生成スキップ: {e}")
        return []


def load_latest_trends(trends_dir: str) -> list[dict]:
    """最新のトレンドJSONを読み込み、スコア順にソートして返す"""
    trends_path = Path(trends_dir)
    if not trends_path.exists():
        return []

    json_files = sorted(trends_path.glob("*.json"), reverse=True)
    if not json_files:
        return []

    with open(json_files[0], encoding="utf-8") as f:
        data = json.load(f)

    keywords = data.get("keywords", [])
    return sorted(keywords, key=lambda x: x.get("score", 0), reverse=True)


def generate_article(client: ClaudeClient, keyword: str, genre: str) -> str:
    """1キーワードについて記事を生成し、必須構造を保証して返す"""
    user_prompt = ARTICLE_TEMPLATE.format(keyword=keyword, genre=genre)
    raw = client.generate(SYSTEM_PROMPT, user_prompt, max_tokens=4096)

    # Markdown除去 + 広告スロット正規化
    article = format_raw_article(raw)

    # 必須要素が欠けていたら補完（冪等）
    article = ensure_article_structure(article, keyword=keyword)

    # 文字数チェック
    char_count = len(article)
    if char_count < MIN_CHAR_COUNT:
        print(f"    ⚠️  警告: 生成記事が短い ({char_count}文字 / 最低{MIN_CHAR_COUNT}文字推奨)")
    else:
        print(f"    文字数: {char_count}文字 ✓")

    return article


def generate_articles(
    client: ClaudeClient,
    trends_dir: str,
    out_dir: str,
    count: int = 3,
) -> list[dict]:
    """トレンドから上位N件の記事を生成"""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    trends = load_latest_trends(trends_dir)
    if not trends:
        print("  トレンドデータがありません。デフォルトキーワードを使用します。")
        trends = [
            {"keyword": "AI副業 始め方", "genre": "AI副業", "score": 10},
            {"keyword": "ChatGPT 活用術", "genre": "AIツール", "score": 9},
            {"keyword": "Docker 初心者 入門", "genre": "Docker", "score": 8},
        ]

    results = []
    for i, trend in enumerate(trends[:count], 1):
        keyword = trend.get("keyword", "AI活用")
        genre = trend.get("genre", "AIツール")
        print(f"  [{i}/{count}] 記事生成中: {keyword} ({genre})")

        article = generate_article(client, keyword, genre)

        safe_keyword = keyword.replace(" ", "_").replace("/", "_")
        filename = f"{today}_{i:03d}_{safe_keyword}.txt"
        filepath = out_path / filename

        filepath.write_text(article, encoding="utf-8")
        print(f"    保存: {filepath}")

        # SEO ハッシュタグ生成
        print(f"    ハッシュタグ生成中...")
        tags = generate_hashtags(client, keyword, genre)
        if tags:
            print(f"    タグ: {', '.join(tags)}")

        results.append({
            "index": i,
            "keyword": keyword,
            "genre": genre,
            "file": str(filepath),
            "char_count": len(article),
            "tags": tags,
        })

    return results


if __name__ == "__main__":
    from automation.common.config_loader import load_config
    cfg = load_config()
    client = ClaudeClient(cfg.anthropic_api_key)
    results = generate_articles(
        client,
        str(cfg.out_dir / "trends"),
        str(cfg.out_dir / "articles"),
        count=1,
    )
    for r in results:
        print(f"  {r['keyword']}: {r['char_count']}文字 → {r['file']}")
