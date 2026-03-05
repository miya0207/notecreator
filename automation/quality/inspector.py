"""記事自動検査エンジン: PR表記・広告枠・文字数・NG表現・プレーンテキスト・テンプレート準拠"""

import json
import re
from datetime import datetime
from pathlib import Path

# NG表現リスト（誇大広告・景品表示法リスク）
NG_EXPRESSIONS = [
    "絶対", "確実に稼げる", "100%", "必ず儲かる", "誰でも簡単に",
    "今すぐ稼げる", "楽して稼げる", "ノーリスク", "損しない",
    "業界No.1", "世界一", "日本一", "最安値", "効果抜群",
    "奇跡の", "驚異の", "激安", "爆益",
]

# 必須セクション
REQUIRED_SECTIONS = [
    "この記事でわかること",
    "おすすめツール",
    "おすすめサービス",
    "おすすめ",
]

# Markdown / HTML パターン
MARKDOWN_PATTERNS = [
    (r"^#{1,6}\s", "見出し記号 (#)"),
    (r"\*\*[^*]+\*\*", "太字 (**)"),
    (r"^>\s", "引用 (>)"),
    (r"^```", "コードブロック (```)"),
    (r"^\- ", "箇条書き (-)"),
    (r"^\* ", "箇条書き (*)"),
    (r"\[.+\]\(.+\)", "リンク ([text](url))"),
]

HTML_PATTERN = re.compile(r"</?[a-zA-Z][^>]*>")


def check_pr_notation(text: str) -> dict:
    """PR表記チェック: 冒頭に広告表記があるか"""
    first_lines = text[:200]
    if "※本記事には広告が含まれます" in first_lines:
        return {"status": "pass", "detail": "冒頭に広告表記あり"}
    return {"status": "fail", "detail": "「※本記事には広告が含まれます」が冒頭にありません"}


def check_ad_slots(text: str) -> dict:
    """広告枠チェック: 3つのプレースホルダーが存在するか"""
    slots = ["{{A8_LINK_TOP}}", "{{A8_LINK_MID}}", "{{A8_LINK_BOTTOM}}"]
    missing = [s for s in slots if s not in text]
    if not missing:
        return {"status": "pass", "detail": "3箇所すべて存在"}
    return {"status": "fail", "detail": f"不足: {', '.join(missing)}"}


def check_char_count(text: str, minimum: int = 1200) -> dict:
    """文字数チェック"""
    count = len(text)
    if count >= minimum:
        return {"status": "pass", "detail": f"{count}文字"}
    return {"status": "fail", "detail": f"{count}文字 (最低{minimum}文字必要)"}


def check_ng_expressions(text: str) -> dict:
    """NG表現チェック"""
    found = [ng for ng in NG_EXPRESSIONS if ng in text]
    if not found:
        return {"status": "pass", "detail": "検出なし"}
    return {"status": "fail", "detail": f"検出: {', '.join(found)}"}


def check_plain_text(text: str) -> dict:
    """プレーンテキストチェック: Markdown/HTMLが含まれていないか"""
    issues = []
    for line in text.splitlines():
        stripped = line.strip()
        for pattern, name in MARKDOWN_PATTERNS:
            if re.search(pattern, stripped):
                issues.append(name)
                break
        if HTML_PATTERN.search(stripped):
            issues.append("HTMLタグ")

    unique_issues = sorted(set(issues))
    if not unique_issues:
        return {"status": "pass", "detail": "Markdown/HTML記号なし"}
    return {"status": "fail", "detail": f"検出: {', '.join(unique_issues)}"}


def check_template(text: str) -> dict:
    """テンプレート準拠チェック: 必須セクションが存在するか"""
    missing = [s for s in REQUIRED_SECTIONS if s not in text]
    if not missing:
        return {"status": "pass", "detail": "必須セクション全て存在"}
    return {"status": "fail", "detail": f"不足: {', '.join(missing)}"}


def inspect_article(text: str) -> dict:
    """記事を全検査項目でチェック"""
    checks = {
        "pr_notation": check_pr_notation(text),
        "ad_slots": check_ad_slots(text),
        "char_count": check_char_count(text),
        "ng_expressions": check_ng_expressions(text),
        "plain_text": check_plain_text(text),
        "template": check_template(text),
    }
    overall = "pass" if all(c["status"] == "pass" for c in checks.values()) else "fail"
    return {"checks": checks, "overall": overall}


def inspect_and_save(article_path: str, out_dir: str) -> dict:
    """記事ファイルを検査してレポートJSONを保存"""
    path = Path(article_path)
    text = path.read_text(encoding="utf-8")

    result = inspect_article(text)
    result["file"] = str(path)
    result["timestamp"] = datetime.now().isoformat()

    # レポートファイル名を記事ファイル名から生成
    report_name = path.stem + "_report.json"
    report_path = Path(out_dir) / report_name
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


if __name__ == "__main__":
    # テスト用サンプル記事
    sample = """※本記事には広告が含まれます

AIツールで副業を始める方法

最近、AIツールを使った副業が注目されています。
この記事では、初心者でも始められるAI副業の方法を解説します。

■ この記事でわかること

AI副業の種類と始め方
必要なツールと準備するもの
最初の一歩の踏み出し方

AIツールを使えば、文章作成やデータ整理など、
さまざまな作業を効率化できます。

まずは無料で使えるツールから始めてみましょう。

【おすすめツール】
{{A8_LINK_TOP}}

AIを使った副業にはいくつかの種類があります。

ライティング支援
データ分析
画像生成

それぞれの特徴を見ていきましょう。

【おすすめサービス】
{{A8_LINK_MID}}

まとめとして、AI副業は初心者でも始めやすい分野です。
まずは小さく始めて、徐々にスキルを磨いていきましょう。

【おすすめ】
{{A8_LINK_BOTTOM}}
"""
    result = inspect_article(sample)
    print(json.dumps(result, ensure_ascii=False, indent=2))
