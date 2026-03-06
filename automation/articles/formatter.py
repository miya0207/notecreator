"""記事フォーマッター: Claude出力をnote投稿用プレーンテキストに変換"""

import re

# 必須広告スロット: (プレースホルダー, セクション見出し)
_AD_SLOTS = [
    ("{{A8_LINK_TOP}}", "【おすすめツール】"),
    ("{{A8_LINK_MID}}", "【おすすめサービス】"),
    ("{{A8_LINK_BOTTOM}}", "【おすすめ】"),
]


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


def normalize_ad_slots(text: str) -> str:
    """広告スロットの表記を統一する。

    Claudeが {A8_LINK_TOP} (シングルブレース) で出力した場合でも
    {{A8_LINK_TOP}} (ダブルブレース) に正規化する。
    既に正しい形式の場合は変更しない。
    """
    for slot_name in ["A8_LINK_TOP", "A8_LINK_MID", "A8_LINK_BOTTOM"]:
        correct = "{{" + slot_name + "}}"
        single = "{" + slot_name + "}"
        # 既に正しい形式があればスキップ（二重変換防止）
        if correct in text:
            continue
        # シングルブレースを正しい形式に変換
        text = text.replace(single, correct)
    return text


def ensure_article_structure(text: str, keyword: str = "") -> str:
    """記事の必須要素が欠けていたら補完する（冪等: 複数回呼んでも安全）。

    補完する要素:
    1. 冒頭のPR表記「※本記事には広告が含まれます」
    2. 「この記事でわかること」セクション
    3. 広告スロット 3箇所 ({{A8_LINK_TOP/MID/BOTTOM}}) と見出し
    """
    result = text

    # 1. PR表記（冒頭200文字内になければ先頭に追加）
    if "※本記事には広告が含まれます" not in result[:300]:
        result = "※本記事には広告が含まれます\n\n" + result

    # 2. 「この記事でわかること」セクション
    if "この記事でわかること" not in result:
        kw = keyword or "このテーマ"
        section = (
            "■ この記事でわかること\n\n"
            f"・{kw}の基本概念がわかる\n"
            "・具体的な活用方法がわかる\n"
            "・次のステップが明確になる\n"
        )
        # 最初の段落（空行区切り）の後に挿入
        idx = result.find("\n\n")
        if idx >= 0:
            result = result[:idx + 2] + section + "\n" + result[idx + 2:]
        else:
            result = result.rstrip("\n") + "\n\n" + section

    # 3. 広告スロット（なければ対応セクション見出しごと末尾に追加）
    for slot, header in _AD_SLOTS:
        if slot not in result:
            result = result.rstrip("\n") + f"\n\n{header}\n{slot}\n"

    return result


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

    # 注意: f-string 内の {{...}} は { に変換されるため、
    # {{A8_LINK_TOP}} → {A8_LINK_TOP} になってしまう。
    # そのため normalize_ad_slots で補正するか、後続の ensure で補完する。
    article = (
        "※本記事には広告が含まれます\n\n"
        f"{title}\n\n"
        f"{introduction}\n\n"
        "■ この記事でわかること\n\n"
        f"{points_text}\n\n"
        f"{body_section1}\n\n"
        "【おすすめツール】\n"
        "{{A8_LINK_TOP}}\n\n"
        f"{body_section2}\n\n"
        "【おすすめサービス】\n"
        "{{A8_LINK_MID}}\n\n"
        f"{summary}\n\n"
        "【おすすめ】\n"
        "{{A8_LINK_BOTTOM}}\n"
    )
    return article


def format_raw_article(raw_text: str) -> str:
    """Claudeの生出力からMarkdownを除去し、広告スロット表記を正規化する"""
    text = strip_markdown(raw_text)
    text = normalize_ad_slots(text)
    # 連続空行を最大2行に制限
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


if __name__ == "__main__":
    # normalize_ad_slots テスト
    sample_single = "本文\n{A8_LINK_TOP}\n本文\n{A8_LINK_MID}\n本文\n{A8_LINK_BOTTOM}"
    normalized = normalize_ad_slots(sample_single)
    print("normalize_ad_slots テスト:")
    print(normalized)
    print()

    # ensure_article_structure テスト（何もない短文に補完）
    short = "AI副業の始め方について解説します。AIを使えば効率的に副業が可能です。"
    ensured = ensure_article_structure(short, keyword="AI副業")
    print("ensure_article_structure テスト:")
    print(ensured)
    print(f"文字数: {len(ensured)}")
