import json
import os
from datetime import datetime

MASTER_HEADER = """\
# 指示
あなたは「ServerStart」教材の執筆者です。
次の「ノート仕様」に従って、本文をMarkdownで出力してください。

# 絶対要件
- 出力はMarkdown
- 指定された「type」がfreeの場合: 具体コマンド/具体設定値を避ける
- 指定された「type」がpaidの場合: 実装手順・コマンド・チェックポイント・地雷マップ・復旧ルートを必ず含める
- 末尾に「自己チェック結果（Yes/No）」を付ける

# ノート共通の固定構成（必須）
1. タイトル（30文字以内）
2. このノートでできるようになること（3-5箇条書き）
3. 想定読者 / 前提知識
4. 全体像（ASCII図）
5. 本編（見出し3〜8個）
6. チェックポイント（成功条件・確認方法）
7. よくある詰まりと対処
8. 用語集（5〜15語）
9. 次のノートへの導線（ServerStartのシリーズ内リンク文）
10. 自己チェック結果（Yes/No）

# 文章ルール
- 初心者が怖くない言い換えを必ず入れる
- 各見出しは3〜5文で読みやすく
- 断定できない箇所は選択肢と判断基準を書く
"""

def build_prompt(plan: dict, note: dict) -> str:
    launch = plan.get("launch_plan", {})
    lines = []
    lines.append(MASTER_HEADER)
    lines.append("\n# 事業前提（要約）")
    lines.append(f"- ブランド: {plan.get('brand')}")
    lines.append("- 方式: PC内VM → Ubuntu Server → Docker → アプリ")
    lines.append(f"- ローンチ計画: 0ヶ月目={launch.get('month0')}, 2ヶ月目={launch.get('month2')}, 3ヶ月目={launch.get('month3')}, 4ヶ月目={launch.get('month4')}")
    lines.append("\n# ノート仕様（JSON）")
    lines.append(json.dumps(note, ensure_ascii=False, indent=2))
    lines.append("\n# 出力追加要件（type別）")
    if note["type"] == "free":
        lines.append("- free: コマンド/設定値を出さず、概念・不安解消・詰まり分類・次の導線に集中する")
        lines.append("- free: ただし「次回（有料）で何をやるか」は具体的に\"見出しレベル\"で予告してよい")
    else:
        lines.append("- paid: 実装手順を具体化し、チェックポイントと地雷マップ、復旧ルートを必ず入れる")
        lines.append("- paid: コマンドは最小限で、コピペしやすく。危険操作は注意書きをつける")
    lines.append("\n# 必須要素")
    for m in note.get("must_include", []):
        lines.append(f"- {m}")
    lines.append("\n# 禁止/回避要素")
    for a in note.get("must_avoid", []):
        lines.append(f"- {a}")
    lines.append("\n# ゴール")
    for g in note.get("goal", []):
        lines.append(f"- {g}")
    lines.append("\n# 次の導線")
    lines.append(f"- 次ノートID: {note.get('cta_next')}")

    # ── 自己検証チェックリスト（出力末尾への強制付与） ──
    lines.append("\n# 【必須】自己検証チェックリスト")
    lines.append("出力の末尾に以下のチェックリストを必ず付けてください。")
    lines.append("各項目に Yes / No を記入し、**No が1つでもあれば本文を修正してから最終出力**してください。\n")
    lines.append("| # | チェック項目 | 結果 |")
    lines.append("|---|------------|------|")
    lines.append("| 1 | 必須構成 1〜10（タイトル／できること／想定読者／全体像／本編／チェックポイント／詰まり対処／用語集／導線／自己チェック）がすべて含まれているか | Yes / No |")

    if note["type"] == "free":
        lines.append("| 2 | type=free の禁止事項（コマンド・具体設定値・ポート番号など）が**一切混入していない**か | Yes / No |")
        lines.append("| 3 | type=free のため「地雷マップ／復旧ルート」は不要 → 代わりに「詰まりの原因カテゴリのみ」になっているか | Yes / No |")
    else:
        lines.append("| 2 | type=paid の必須要素（チェックポイント・地雷マップ・復旧ルート）がすべて入っているか | Yes / No |")
        lines.append("| 3 | 危険操作（rm・prune・上書きなど）に ⚠️ 注意書きが付いているか | Yes / No |")

    lines.append("| 4 | 初心者向け言い換え・比喩・例えが**本文中に5回以上**入っているか | Yes / No |")
    lines.append("| 5 | 「次のノートへの導線」セクションで次ノートのタイトルと内容予告が明確に書かれているか | Yes / No |")
    lines.append("\n> ⚠️ No が残っている場合は該当箇所を修正し、修正済みの完全な本文を出力してください。")

    return "\n".join(lines)

def main():
    with open("plan.json", "r", encoding="utf-8") as f:
        plan = json.load(f)

    out_dir = "out_prompts"
    os.makedirs(out_dir, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    index_lines = [f"# Prompt Index ({stamp})", ""]

    for note in plan["notes"]:
        filename = f"{note['id']}_{note['type']}.txt"
        prompt = build_prompt(plan, note)
        with open(os.path.join(out_dir, filename), "w", encoding="utf-8") as wf:
            wf.write(prompt)
        index_lines.append(f"- {filename}: {note['title']}")

    with open(os.path.join(out_dir, "INDEX.md"), "w", encoding="utf-8") as wf:
        wf.write("\n".join(index_lines))

    print(f"Generated prompts in ./{out_dir}/")
    print("\n".join(index_lines))

if __name__ == "__main__":
    main()
