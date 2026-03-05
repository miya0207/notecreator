"""SEOトレンド収集AI: 複数データソースからIT初心者向けキーワードを収集・スコアリング"""

import json
from datetime import date
from pathlib import Path

import requests

from automation.common.claude_client import ClaudeClient

REQUEST_TIMEOUT = 15
USER_AGENT = "notecreator-trend-bot/1.0"


def fetch_hackernews(limit: int = 30) -> list[str]:
    """HackerNews トップ記事のタイトルを取得"""
    try:
        resp = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        story_ids = resp.json()[:limit]

        titles = []
        for sid in story_ids:
            r = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                timeout=REQUEST_TIMEOUT,
            )
            if r.ok:
                item = r.json()
                if item and item.get("title"):
                    titles.append(item["title"])
        return titles
    except Exception as e:
        print(f"  HackerNews取得エラー: {e}")
        return []


def fetch_reddit(subreddit: str = "technology", limit: int = 25) -> list[str]:
    """Reddit ホット記事のタイトルを取得"""
    try:
        resp = requests.get(
            f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}",
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            post["data"]["title"]
            for post in data.get("data", {}).get("children", [])
            if post.get("data", {}).get("title")
        ]
    except Exception as e:
        print(f"  Reddit取得エラー: {e}")
        return []


def fetch_qiita(limit: int = 20) -> list[dict]:
    """Qiita トレンド記事のタイトル＋タグを取得"""
    try:
        resp = requests.get(
            "https://qiita.com/api/v2/items",
            params={"per_page": limit, "query": "tag:AI OR tag:Docker OR tag:Linux OR tag:初心者"},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        items = resp.json()
        return [
            {
                "title": item["title"],
                "tags": [t["name"] for t in item.get("tags", [])],
            }
            for item in items
        ]
    except Exception as e:
        print(f"  Qiita取得エラー: {e}")
        return []


def fetch_zenn(limit: int = 20) -> list[dict]:
    """Zenn トレンド記事のタイトル＋トピックを取得"""
    try:
        resp = requests.get(
            "https://zenn.dev/api/articles",
            params={"order": "trend", "count": limit},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        articles = data.get("articles", [])
        return [
            {
                "title": a.get("title", ""),
                "topics": [a.get("topic", {}).get("name", "")] if a.get("topic") else [],
            }
            for a in articles
        ]
    except Exception as e:
        print(f"  Zenn取得エラー: {e}")
        return []


def collect_raw_data() -> dict:
    """全データソースから生データを収集"""
    print("  HackerNews...")
    hn = fetch_hackernews()
    print(f"    {len(hn)}件取得")

    print("  Reddit...")
    reddit = fetch_reddit()
    print(f"    {len(reddit)}件取得")

    print("  Qiita...")
    qiita = fetch_qiita()
    print(f"    {len(qiita)}件取得")

    print("  Zenn...")
    zenn = fetch_zenn()
    print(f"    {len(zenn)}件取得")

    return {
        "hackernews": hn,
        "reddit": reddit,
        "qiita": qiita,
        "zenn": zenn,
    }


SCORING_SYSTEM_PROMPT = """\
あなたはSEOアナリストです。
IT初心者向けのnote記事のキーワード選定を支援します。
"""

SCORING_USER_PROMPT = """\
以下のデータソースから収集した記事タイトルを分析し、
「AI × IT初心者」ジャンルのnote記事で使えるキーワードを抽出・スコアリングしてください。

対象ジャンル:
{genres}

収集データ:
{raw_data}

以下のJSON形式で、キーワード10〜15個を返してください。
重複やほぼ同じ意味のキーワードは統合してください。

```json
{{
  "keywords": [
    {{
      "keyword": "AI副業 始め方",
      "genre": "AI副業",
      "search_demand": 8,
      "competition": 5,
      "beginner_demand": 9,
      "score": 14.4,
      "reason": "AI副業への関心が高まっており初心者需要が大きい"
    }}
  ]
}}
```

スコア計算: score = search_demand × beginner_demand / competition
search_demand: 検索需要 (1-10)
competition: 競合強度 (1-10、高いほど競合が強い)
beginner_demand: 初心者需要 (1-10)
"""


def score_keywords(
    client: ClaudeClient,
    raw_data: dict,
    genres: list[dict],
) -> list[dict]:
    """Claude APIでキーワードをスコアリング"""
    genres_text = "\n".join(f"- {g['name']}: {', '.join(g.get('keywords', []))}" for g in genres)

    # 生データを要約（トークン節約）
    summary_parts = []
    for source, data in raw_data.items():
        if isinstance(data, list) and data:
            if isinstance(data[0], str):
                titles = data[:15]
                summary_parts.append(f"[{source}]\n" + "\n".join(f"- {t}" for t in titles))
            elif isinstance(data[0], dict):
                items = data[:15]
                lines = []
                for item in items:
                    title = item.get("title", "")
                    tags = item.get("tags", item.get("topics", []))
                    lines.append(f"- {title} (tags: {', '.join(tags)})")
                summary_parts.append(f"[{source}]\n" + "\n".join(lines))

    raw_text = "\n\n".join(summary_parts)
    user_prompt = SCORING_USER_PROMPT.format(genres=genres_text, raw_data=raw_text)

    result = client.generate_json(SCORING_SYSTEM_PROMPT, user_prompt)
    return result.get("keywords", [])


def collect_trends(
    client: ClaudeClient,
    genres: list[dict],
    out_dir: str,
) -> dict:
    """トレンド収集→スコアリング→保存"""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    print("  データソースから収集中...")
    raw_data = collect_raw_data()

    print("  キーワードスコアリング中...")
    keywords = score_keywords(client, raw_data, genres)

    # スコア順ソート
    keywords.sort(key=lambda x: x.get("score", 0), reverse=True)

    result = {
        "date": today,
        "sources": list(raw_data.keys()),
        "source_counts": {k: len(v) for k, v in raw_data.items()},
        "keywords": keywords,
    }

    filepath = out_path / f"{today}_trends.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  保存: {filepath} ({len(keywords)}キーワード)")
    return result


if __name__ == "__main__":
    from automation.common.config_loader import load_config
    cfg = load_config()
    client = ClaudeClient(cfg.anthropic_api_key)
    result = collect_trends(
        client,
        cfg.topics["genres"],
        str(cfg.out_dir / "trends"),
    )
    print(f"\n上位5キーワード:")
    for kw in result["keywords"][:5]:
        print(f"  {kw['keyword']} (score: {kw['score']}, genre: {kw['genre']})")
