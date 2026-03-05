"""note収益導線AI: 無料記事から有料note企画を生成"""

import json
from datetime import date
from pathlib import Path

from automation.common.claude_client import ClaudeClient

SYSTEM_PROMPT = """\
あなたはnoteの有料コンテンツ企画のプロフェッショナルです。
無料記事を読んだ読者が「もっと知りたい」と思うような有料noteを企画します。
対象読者はIT初心者です。
"""

USER_PROMPT = """\
以下の無料記事の内容をもとに、有料noteの企画を作成してください。

無料記事キーワード: {keyword}
無料記事ジャンル: {genre}
無料記事の文字数: 約{char_count}文字

以下のJSON形式で返してください:

```json
{{
  "keyword": "{keyword}",
  "genre": "{genre}",
  "premium_note": {{
    "title": "有料noteタイトル（30文字以内）",
    "subtitle": "サブタイトル（購入を後押しする一言）",
    "target_reader": "想定読者（1文）",
    "toc": [
      "第1章: 章タイトル",
      "第2章: 章タイトル",
      "第3章: 章タイトル",
      "第4章: 章タイトル",
      "第5章: 章タイトル"
    ],
    "estimated_pages": 15,
    "price_recommendation": {{
      "price": 1980,
      "reason": "価格設定の理由"
    }},
    "price_options": [980, 1980, 2980],
    "upsell_text": "無料記事の末尾に追加するアップセル文（5行以内）"
  }}
}}
```

ルール:
- 無料記事の内容を深掘りする構成にする
- 初心者が「これなら買う価値がある」と思える内容にする
- 目次は5〜8章で構成
- アップセル文は押し売り感を出さず、自然な導線にする
- 価格は980円/1980円/2980円のいずれかを推奨
"""


def generate_premium_plan(
    client: ClaudeClient,
    keyword: str,
    genre: str,
    char_count: int,
    out_dir: str,
    index: int = 1,
) -> dict:
    """有料note企画を生成して保存"""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    user_prompt = USER_PROMPT.format(
        keyword=keyword,
        genre=genre,
        char_count=char_count,
    )

    result = client.generate_json(SYSTEM_PROMPT, user_prompt)
    result["date"] = today

    safe_keyword = keyword.replace(" ", "_").replace("/", "_")
    filename = f"{today}_{index:03d}_{safe_keyword}_premium.json"
    filepath = out_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"    有料note企画保存: {filepath}")
    return result


if __name__ == "__main__":
    from automation.common.config_loader import load_config
    cfg = load_config()
    client = ClaudeClient(cfg.anthropic_api_key)
    result = generate_premium_plan(
        client,
        keyword="AI副業 始め方",
        genre="AI副業",
        char_count=1800,
        out_dir=str(cfg.out_dir / "premium"),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
