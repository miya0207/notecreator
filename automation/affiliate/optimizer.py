"""アフィリエイト最適化AI: 記事テーマから広告候補とA8検索キーワードを生成"""

import json
from datetime import date
from pathlib import Path

from automation.common.claude_client import ClaudeClient

SYSTEM_PROMPT = """\
あなたはアフィリエイト広告の最適化アドバイザーです。
IT初心者向けnote記事に適した広告候補を提案します。
景品表示法を遵守し、誇大広告は提案しません。
"""

USER_PROMPT = """\
以下の記事テーマに最適な広告候補を提案してください。

記事キーワード: {keyword}
記事ジャンル: {genre}

既存の広告カテゴリ:
{categories}

以下のJSON形式で返してください:

```json
{{
  "keyword": "{keyword}",
  "genre": "{genre}",
  "recommendations": [
    {{
      "category": "カテゴリ名",
      "a8_search_keywords": ["キーワード1", "キーワード2", "キーワード3"],
      "recommended_services": ["サービス名1", "サービス名2"],
      "appeal_points": "訴求ポイント（初心者に響く一言）",
      "placement": "TOP/MID/BOTTOM のどこに配置すべきか"
    }}
  ]
}}
```

ルール:
- 記事テーマに関連性の高い広告を3つ提案
- A8検索キーワードは実際にA8.netで検索して見つかりそうなものを提案
- 初心者が「これ使ってみよう」と思える訴求ポイントを書く
- 誇大広告にならない表現を使う
"""


def generate_affiliate_suggestions(
    client: ClaudeClient,
    keyword: str,
    genre: str,
    categories: list[dict],
    out_dir: str,
    index: int = 1,
) -> dict:
    """記事テーマから広告候補を生成して保存"""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    categories_text = "\n".join(
        f"- {c['theme']}: サービス={', '.join(c.get('services', []))}, "
        f"A8キーワード={', '.join(c.get('a8_keywords', []))}"
        for c in categories
    )

    user_prompt = USER_PROMPT.format(
        keyword=keyword,
        genre=genre,
        categories=categories_text,
    )

    result = client.generate_json(SYSTEM_PROMPT, user_prompt)
    result["date"] = today

    safe_keyword = keyword.replace(" ", "_").replace("/", "_")
    filename = f"{today}_{index:03d}_{safe_keyword}_affiliate.json"
    filepath = out_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"    広告候補保存: {filepath}")
    return result


if __name__ == "__main__":
    from automation.common.config_loader import load_config
    cfg = load_config()
    client = ClaudeClient(cfg.anthropic_api_key)
    result = generate_affiliate_suggestions(
        client,
        keyword="AI副業 始め方",
        genre="AI副業",
        categories=cfg.affiliate["categories"],
        out_dir=str(cfg.out_dir / "affiliate"),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
