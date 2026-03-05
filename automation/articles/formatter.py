"""記事フォーマッター: Claude出力をnote投稿用プレーンテキストに変換"""

import re


def strip_markdown(text: str) -> str:
    """Markdown記号を除去してプレーンテキストに変換"""
    lines = text.splitlines()
    cleaned = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()

        # コードブロック除去
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # 見出し記号除去 (# ## ### etc.)
        line = re.sub(r"^#{1,6}\s+", "", line)

        # 太字/斜体除去
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        line = re.sub(r"\*([^*]+)\*", r"\1", line)
        line = re.sub(r"__([^_]+)__", r"\1", line)

        # リンク記法除去 [text](url) → text
        line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)

        # 引用記号除去
        line = re.sub(r"^>\s*", "", line)

        # 箇条書き記号を変換 (- or * → ・)
        line = re.sub(r"^[\-\*]\s+", "・", line)

        # HTMLタグ除去
        line = re.sub(r"</?[a-zA-Z][^>]*>", "", line)

        # インラインコード除去
        line = re.sub(r"`([^`]+)`", r"\1", line)

        cleaned.append(line)

    return "\n".join(cleaned)


def format_article(
    title: str,
    introduction: str,
    key_points: list[str],
    body_section1: str,
    body_section2: str,
    summary: str,
) -> str:
    """記事テンプレートに沿ってプレーンテキスト記事を組み立てる"""
    points_text = "\n".join(f"・{p}" for p in key_points)

    article = f"""※本記事には広告が含まれます

{title}

{introduction}

■ この記事でわかること

{points_text}

{body_section1}

【おすすめツール】
{{{{A8_LINK_TOP}}}}

{body_section2}

【おすすめサービス】
{{{{A8_LINK_MID}}}}

{summary}

【おすすめ】
{{{{A8_LINK_BOTTOM}}}}
"""
    return article


def format_raw_article(raw_text: str) -> str:
    """Claudeの生出力からMarkdownを除去してプレーンテキスト化"""
    text = strip_markdown(raw_text)
    # 連続空行を最大2行に制限
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


if __name__ == "__main__":
    sample = format_article(
        title="AI副業の始め方ガイド",
        introduction="最近、AIを使った副業が注目されています。この記事では初心者向けに解説します。",
        key_points=["AI副業の種類がわかる", "必要なツールがわかる", "始め方の手順がわかる"],
        body_section1="AIツールには文章生成、画像生成、データ分析など様々な種類があります。\n\n初心者におすすめなのは、ChatGPTを使ったライティング支援です。",
        body_section2="副業を始めるには、まずクラウドソーシングサイトに登録しましょう。\n\nランサーズやクラウドワークスが有名です。",
        summary="AI副業は初心者でも始めやすい分野です。まずは小さく始めて、実績を積んでいきましょう。",
    )
    print(sample)
