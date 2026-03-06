"""Threads投稿文言生成: note の投稿 URL を含む Threads投稿用テキストを生成する。"""


def generate_threads_text(
    keyword: str,
    article_url: str,
    genre: str = "",
    preview: str = "",
) -> str:
    """note URL付きのThreads投稿文言を生成する。

    Args:
        keyword: 記事キーワード
        article_url: note 投稿後の記事 URL
        genre: ジャンル（オプション、テンプレート選択用）
        preview: 記事プレビューテキスト（オプション）

    Returns:
        Threads投稿用の文言（コピペ用）
    """
    if not article_url:
        article_url = "https://note.com/your-page"

    # テンプレート選択（ジャンルごと）
    if genre == "IT初心者":
        template = f"""IT初心者向け｛keyword｝完全ガイド

近年、{keyword}への関心が急速に高まっています。特に初心者の方からも「試してみたい」という声が増えており、当noteでは基礎から丁寧に解説しています。

この記事を読むことで、{keyword}の全体像が把握でき、最初の一歩を踏み出す準備が整います。

続きはnote👇
{article_url}"""

    elif genre == "AIツール" or genre == "AI副業":
        template = f"""{keyword}の完全攻略ガイド

{keyword}について知りたい方へ。本当に必要な基礎知識から実践方法までを、初心者向けにまとめました。

この記事を読むことで、{keyword}の活用方法が分かり、実際に取り組む準備ができます。

続きはnote👇
{article_url}"""

    else:
        # デフォルト
        template = f"""{keyword}の完全入門ガイド

{keyword}について詳しく知りたい方へ。基礎から実践まで、体系的に解説した記事を書きました。

この記事を読むことで、{keyword}の全体像が分かり、次のステップへ進む準備ができます。

続きはnote👇
{article_url}"""

    return template


def generate_threads_text_with_preview(
    keyword: str,
    article_url: str,
    genre: str = "",
    char_limit: int = 280,  # Threads の文字制限（参考）
) -> str:
    """より詳しいThreads投稿文言を生成（記事プレビュー付き）。

    Args:
        keyword: 記事キーワード
        article_url: note 投稿後の記事 URL
        genre: ジャンル
        char_limit: Threads文字制限（参考値）

    Returns:
        Threads投稿用の文言
    """
    # シンプル版
    base_text = generate_threads_text(keyword, article_url, genre)

    # 文字数制限に合わせてトリミング（必要に応じて）
    if len(base_text) > char_limit:
        # 最後の行（note URL）は必ず含める
        url_part = f"\n\n続きはnote👇\n{article_url}"
        remaining = char_limit - len(url_part)
        if remaining > 50:
            trimmed = base_text[: remaining - 3] + "..." + url_part
            return trimmed
    return base_text
