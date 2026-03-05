"""Threads投稿生成: 記事からSNS投稿テキストを生成"""

from datetime import date
from pathlib import Path

from automation.common.claude_client import ClaudeClient

SYSTEM_PROMPT = """\
あなたはSNSマーケターです。
IT初心者向けnote記事の宣伝用Threads投稿を作成します。
"""

USER_PROMPT = """\
以下のnote記事の宣伝用Threads投稿を作成してください。

記事キーワード: {keyword}
記事ジャンル: {genre}

ルール:
- 300文字以内（厳守）
- 読者の興味を引くフック（疑問文や驚きの事実）で始める
- 記事の要点を2〜3行で凝縮
- 最後に必ず以下を追加:
  続きはnote👇
  <<NOTE_URL>>
- 絵文字は1〜2個まで（使いすぎない）
- 誇大表現は禁止
- プレーンテキストで出力（Markdown/HTMLは使わない）

投稿テキストのみを出力してください。余計な説明は不要です。
"""


def generate_threads_post(
    client: ClaudeClient,
    keyword: str,
    genre: str,
    out_dir: str,
    index: int = 1,
) -> str:
    """Threads投稿テキストを生成して保存"""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    user_prompt = USER_PROMPT.format(keyword=keyword, genre=genre)
    post = client.generate(SYSTEM_PROMPT, user_prompt, max_tokens=500)
    post = post.strip()

    # 300文字超過チェック
    if len(post) > 300:
        # 末尾の導線部分を保持しつつ切り詰め
        suffix = "\n\n続きはnote👇\n<<NOTE_URL>>"
        body_limit = 300 - len(suffix)
        post = post[:body_limit].rsplit("\n", 1)[0] + suffix

    safe_keyword = keyword.replace(" ", "_").replace("/", "_")
    filename = f"{today}_{index:03d}_{safe_keyword}_threads.txt"
    filepath = out_path / filename

    filepath.write_text(post, encoding="utf-8")
    print(f"    Threads投稿保存: {filepath} ({len(post)}文字)")
    return post


if __name__ == "__main__":
    from automation.common.config_loader import load_config
    cfg = load_config()
    client = ClaudeClient(cfg.anthropic_api_key)
    post = generate_threads_post(
        client,
        keyword="AI副業 始め方",
        genre="AI副業",
        out_dir=str(cfg.out_dir / "threads"),
    )
    print(post)
