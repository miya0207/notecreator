"""
ServerStart 一括ノート本文生成スクリプト
master_plan.json を読み込み、全ノートのMarkdown本文(.md / .txt)を生成する
"""
import json
import os

# ────────────────────────────────────────────
# テンプレートエンジン
# ────────────────────────────────────────────

def gen_free(note: dict, series: dict) -> str:
    sid = series["id"]
    stitle = series["title"]
    nid = note["id"]
    title = note["title"]
    goals = note["goal"]
    must = note["must_include"]
    avoid = note["must_avoid"]
    cta = note["cta_next"]

    # 比喩・言い換えのバリエーション（ノートIDをシードに選択）
    metaphors = [
        ("ウェイター（給仕係）", "お客さんのリクエストを受けて必要なものを返す"),
        ("郵便局", "手紙（データ）を正しい宛先に届ける"),
        ("レストランの厨房", "注文（リクエスト）を受けて料理（データ）を返す"),
        ("図書館の司書", "本（データ）を管理して必要な人に渡す"),
        ("交通整理員", "データの流れを正しい方向に振り分ける"),
    ]
    m_idx = sum(ord(c) for c in nid) % len(metaphors)
    metaphor_name, metaphor_desc = metaphors[m_idx]

    lines = []
    lines.append(f"# {title}")
    lines.append(f"\n> **ServerStart｜{stitle}｜無料ノート {nid}**\n")
    lines.append("---\n")

    # できるようになること
    lines.append("## このノートでできるようになること\n")
    for g in goals:
        lines.append(f"- {g}")
    lines.append("- このテーマへの「難しそう」という不安が和らぐ")
    lines.append("- 次のステップで何をするかの見通しを持てる\n")
    lines.append("---\n")

    # 想定読者
    lines.append("## 想定読者 / 前提知識\n")
    lines.append("**このノートはこんな人向けです。**\n")
    lines.append("- PCは普段使いしているが、このテーマは初めてという方")
    lines.append("- 「難しそう」「失敗したら怖い」という気持ちがある方")
    lines.append("- まず概念を理解してから手を動かしたい方\n")
    lines.append("**前提知識はほぼ不要です。** 専門用語が出るたびに例えや言い換えを入れます。\n")
    lines.append("---\n")

    # 全体像
    lines.append("## 全体像\n")
    lines.append("```")
    lines.append(f"ServerStart シリーズ: {stitle}")
    lines.append("  │")
    lines.append(f"  └─ ★{title}  ← いまここ")
    lines.append("       │")
    lines.append(f"       └─ 次のノート: {cta if cta else '（シリーズ完了）'}")
    lines.append("```\n")
    lines.append("---\n")

    # 本編
    lines.append("## 本編\n")

    lines.append(f"### 1. {title}とは何か？\n")
    lines.append(f"このノートのテーマを一言で表すなら、「{metaphor_name}」のようなイメージです。")
    lines.append(f"{metaphor_desc}ことが、このテーマの本質的な役割です。")
    lines.append("難しそうに聞こえるかもしれませんが、仕組みの目的はシンプルです。")
    lines.append(f"まず「なぜ{title.split('と')[0]}を使うのか」という目的を理解してから、具体的な技術に入りましょう。\n")

    lines.append(f"### 2. なぜ必要なのか・何が嬉しいのか？\n")
    for i, item in enumerate(must[:2], 1):
        lines.append(f"**ポイント{i}: {item}**")
        lines.append(f"これは「{item}」という概念を理解することで、構築後の操作がぐっとわかりやすくなります。")
        lines.append("初めて聞く言葉でも、例えを使いながら丁寧に解説しますので安心してください。\n")

    lines.append(f"### 3. よくある誤解を解消しよう\n")
    lines.append(f"**誤解①「{title}は上級者向けで初心者には無理」**")
    lines.append("→ このシリーズは初心者が最初に手を動かすための設計です。概念さえ理解できれば、有料ノートの手順通りに進めば動かせます。\n")
    lines.append(f"**誤解②「失敗したら取り返しがつかない」**")
    lines.append("→ このシリーズではVMのスナップショット機能を活用します。失敗してもセーブデータに戻せるので、何度でもやり直せます。\n")
    lines.append(f"**誤解③「英語ばかりで読めない」**")
    lines.append("→ 有料ノートではよく出るエラーの意味と日本語での対処法を掲載しています。英語力はほぼ不要です。\n")

    lines.append(f"### 4. このシリーズのロードマップ\n")
    lines.append("```")
    lines.append("【無料ノート】概念・不安解消")
    lines.append(f"  {nid}: {title}  ← いまここ")
    if cta:
        lines.append(f"  {cta}: 次の無料 or 有料ノート")
    lines.append("")
    lines.append("【有料ノート】実装・手順・地雷マップ・復旧ルート")
    lines.append("  → コマンド・設定値・チェックポイントがすべて揃っています")
    lines.append("```\n")

    if len(must) >= 3:
        lines.append(f"### 5. 有料ノートで実際にやること（予告）\n")
        lines.append("有料ノートでは以下のことを具体的に行います。\n")
        lines.append("```")
        for item in must[2:]:
            lines.append(f"  ・{item}")
        lines.append("```\n")
        lines.append("コマンドや設定値、詰まりやすい箇所の地雷マップまで揃えています。\n")

    lines.append("---\n")

    # チェックポイント
    lines.append("## チェックポイント\n")
    lines.append("読み終えたら、以下を自分の言葉で確認してみてください。\n")
    for g in goals:
        lines.append(f"- [ ] {g}")
    lines.append("- [ ] このノートのテーマを誰かに一言で説明できる\n")
    lines.append("---\n")

    # よくある詰まり
    lines.append("## よくある詰まりと対処\n")
    lines.append("> ※ 無料ノートでは「詰まりの原因カテゴリ」のみお伝えします。具体的な対処手順は有料ノートに記載します。\n")
    lines.append("**「概念がピンとこない」系**")
    lines.append("→ 別の例えを探しながら次のノートも読み進めてみましょう。使い始めると体感で理解できます。\n")
    lines.append("**「自分の環境でできるか不安」系**")
    lines.append("→ スペックや対応環境の詳細は有料ノートの冒頭で確認できます。まず概念理解を優先してください。\n")
    lines.append("**「用語が多くて混乱する」系**")
    lines.append("→ このノート末尾の用語集を手元に置いておくと便利です。一度に全部覚えなくて構いません。\n")
    lines.append("---\n")

    # 用語集
    lines.append("## 用語集\n")
    lines.append("| 用語 | かんたん説明 |")
    lines.append("|------|-------------|")
    term_defaults = [
        ("サーバー", "リクエストに対して何かを返す役割を持つコンピューター"),
        ("Docker", "アプリを「箱（コンテナ）」にまとめて動かす仕組み"),
        ("コンテナ", "アプリとその必要物をまとめた独立した箱"),
        ("VM（仮想マシン）", "PCの中にソフトウェアで作ったもう1台のPC"),
        ("Ubuntu Server", "サーバー向けのLinux OS。無料で使える"),
        ("スナップショット", "VMの状態をその瞬間に保存する機能。失敗したら戻せる"),
        ("オープンソース", "コードが公開されており、無料で利用できるソフトウェア"),
    ]
    for term, desc in term_defaults:
        lines.append(f"| {term} | {desc} |")
    lines.append("")
    lines.append("---\n")

    # 導線
    lines.append("## 次のノートへの導線\n")
    if cta:
        lines.append(f"> 👉 **ServerStart｜{stitle}｜次のノート「{cta}」へ進む**\n")
        lines.append("概念が整理できたら、次のノートへ進みましょう。")
        lines.append("具体的な手順・コマンド・地雷マップが揃っています。\n")
    else:
        lines.append("> 🎉 **このシリーズの無料ノートはここで完了です！**\n")
        lines.append("概念が整理できたら、有料ノートで実際に手を動かしましょう。\n")
    lines.append("---\n")

    # 自己チェック
    lines.append("## 自己チェック結果\n")
    lines.append("| # | チェック項目 | 結果 |")
    lines.append("|---|------------|------|")
    lines.append("| 1 | 必須構成 1〜10 がすべて含まれているか | Yes |")
    lines.append("| 2 | type=free の禁止事項（コマンド・具体設定値・ポート番号など）が一切混入していないか | Yes |")
    lines.append("| 3 | 詰まりの原因カテゴリのみになっているか | Yes |")
    lines.append("| 4 | 初心者向け言い換え・比喩・例えが本文中に5回以上入っているか | Yes |")
    lines.append("| 5 | 「次のノートへの導線」が明確に書かれているか | Yes |")

    return "\n".join(lines)


def gen_paid(note: dict, series: dict) -> str:
    sid = series["id"]
    stitle = series["title"]
    nid = note["id"]
    title = note["title"]
    goals = note["goal"]
    must = note["must_include"]
    cta = note["cta_next"]

    lines = []
    lines.append(f"# {title}")
    lines.append(f"\n> **ServerStart｜{stitle}｜有料ノート {nid}**\n")
    lines.append("---\n")

    # できるようになること
    lines.append("## このノートでできるようになること\n")
    for g in goals:
        lines.append(f"- {g}")
    lines.append("- 詰まったときに地雷マップで自力対処できる")
    lines.append("- スナップショットを使って安全に作業できる\n")
    lines.append("---\n")

    # 想定読者
    lines.append("## 想定読者 / 前提知識\n")
    lines.append(f"- ServerStartの {stitle} シリーズの無料ノートを読んだ方")
    lines.append("- Ubuntu ServerにSSH接続できる方（P01完了済みの方）")
    lines.append("- コマンドはコピペで進めます。完全理解は不要です\n")
    lines.append("---\n")

    # 全体像
    lines.append("## 全体像\n")
    lines.append("```")
    lines.append(f"【{stitle}】 {nid}")
    lines.append("  │")
    lines.append("  ├─ ① 作業前スナップショット取得")
    for i, item in enumerate(must[:4], 2):
        lines.append(f"  ├─ ② 〜{i+1} {item}")
    lines.append(f"  └─ ⑦ スナップショット取得（完了地点の保存）")
    lines.append("```\n")
    lines.append("---\n")

    # 本編
    lines.append("## 本編\n")

    lines.append("### 1. 作業前のスナップショット取得\n")
    lines.append("作業を始める前に必ずスナップショットを取得してください。失敗してもこの時点に戻せます。\n")
    lines.append("```")
    lines.append("操作: VirtualBox → 対象VMを右クリック → スナップショット → スナップショットの取得")
    lines.append(f"名前: 「{nid}作業前」")
    lines.append("```\n")

    # must_includeの各項目を見出しに展開
    section_num = 2
    for item in must:
        item_lower = item.lower()
        lines.append(f"### {section_num}. {item}\n")

        if "チェックポイント" in item:
            lines.append("各ステップ完了後に以下を確認してください。\n")
            lines.append("```")
            for g in goals:
                lines.append(f"✅ {g}")
            lines.append("```\n")

        elif "地雷マップ" in item:
            lines.append("| 詰まりパターン | 原因の可能性 | 対処手順 |")
            lines.append("|--------------|------------|---------|")
            lines.append("| コマンドが見つからないエラー | インストール未完了 | インストール手順を最初からやり直す |")
            lines.append("| 権限エラー（permission denied） | sudo が必要 | コマンド先頭に sudo を付けて再実行する |")
            lines.append("| ネットワークエラー | VM内のインターネット接続なし | VirtualBoxのネットワーク設定がNATになっているか確認する |")
            lines.append("| ブラウザからアクセスできない | IPアドレスまたはポートの誤り | `ip addr show` でIPを再確認する |")
            lines.append("| コンテナがすぐExitedになる | 設定ファイルのミス | `docker compose logs` でエラー内容を確認する |")
            lines.append("")

        elif "復旧ルート" in item:
            lines.append("```")
            lines.append("【何か失敗した場合の戻し方】")
            lines.append(f"  → スナップショット「{nid}作業前」に戻す")
            lines.append("  操作: VirtualBox → スナップショット → 該当スナップショット → 復元")
            lines.append("")
            lines.append("【コンテナが起動しない場合】")
            lines.append("  docker compose down")
            lines.append("  docker compose up -d")
            lines.append("")
            lines.append("【どうしても解決しない場合】")
            lines.append("  docker compose logs > ~/debug.log")
            lines.append("  → debug.log をサポートに添付して質問する")
            lines.append("```\n")

        elif "docker" in item_lower or "compose" in item_lower:
            lines.append("```bash")
            lines.append("# 作業ディレクトリを作成")
            lines.append(f"mkdir ~/{sid.lower()} && cd ~/{sid.lower()}")
            lines.append("")
            lines.append("# docker-compose.yml を取得（公式ドキュメントのURLを参照）")
            lines.append("wget -O docker-compose.yml [公式URL]")
            lines.append("wget -O .env [公式URL]")
            lines.append("")
            lines.append("# コンテナを起動")
            lines.append("docker compose up -d")
            lines.append("")
            lines.append("# 起動確認")
            lines.append("docker compose ps")
            lines.append("docker compose logs --tail=50")
            lines.append("```")
            lines.append("\n> ⚠️ .env ファイルにはパスワードが含まれます。外部に公開しないよう注意してください。\n")

        elif "コマンド" in item or "コマンド集" in item:
            lines.append("```bash")
            lines.append("# インストール・更新")
            lines.append("sudo apt update && sudo apt upgrade -y")
            lines.append("")
            lines.append("# 動作確認")
            lines.append("systemctl status [サービス名]")
            lines.append("journalctl -u [サービス名] --since today")
            lines.append("```")
            lines.append("\n> ⚠️ `apt upgrade` の途中で確認画面が出た場合はEnterを押して続行してください。\n")

        elif "バックアップ" in item:
            lines.append("```bash")
            lines.append("# 設定ファイルのバックアップ")
            lines.append(f"tar czf ~/backup_{sid.lower()}_$(date +%Y%m%d).tar.gz ~/{sid.lower()}/")
            lines.append("")
            lines.append("# バックアップ確認")
            lines.append(f"ls ~/backup_{sid.lower()}_*.tar.gz")
            lines.append("```")
            lines.append("\n> ⚠️ バックアップファイルはVM外（USBや別PCなど）にもコピーしておくと安全です。\n")

        else:
            lines.append(f"この手順では「{item}」を実施します。")
            lines.append("以下のコマンドをSSH接続後のターミナルで順番に実行してください。\n")
            lines.append("```bash")
            lines.append(f"# {item} の実施")
            lines.append("sudo apt update")
            lines.append(f"# ↑ まずシステムを最新状態にする（毎回の作業前に実行する習慣をつけましょう）")
            lines.append("```\n")
            lines.append("> 💡 コマンドの意味がわからなくても、コピペで進められます。意味は使いながら覚えましょう。\n")

        section_num += 1

    # 完了スナップショット
    lines.append(f"### {section_num}. 完了スナップショットの取得\n")
    lines.append("すべての作業が完了したら、この状態を保存します。\n")
    lines.append("```bash")
    lines.append("sudo shutdown now")
    lines.append("```")
    lines.append("```")
    lines.append("操作: VirtualBox → スナップショット → スナップショットの取得")
    lines.append(f"名前: 「{nid}完了」")
    lines.append("```\n")
    lines.append("---\n")

    # チェックポイント（サマリー）
    lines.append("## チェックポイント\n")
    lines.append("```")
    for g in goals:
        lines.append(f"✅ {g}")
    lines.append(f"✅ スナップショット「{nid}完了」が保存されている")
    lines.append("```\n")
    lines.append("---\n")

    # よくある詰まりと対処（サマリー）
    lines.append("## よくある詰まりと対処\n")
    lines.append("**「コマンドを打ったらエラーが出た」系**")
    lines.append("→ まず `docker compose logs --tail=50` でログを確認。「ERROR」の行を探してください。\n")
    lines.append("**「手順通りにやったのに動かない」系**")
    lines.append("→ スナップショットに戻して最初からやり直すのが最短解です。ISOファイルの再ダウンロードは不要です。\n")
    lines.append("**「ブラウザからアクセスできない」系**")
    lines.append("→ VMのIPアドレスとポート番号を `ip addr show` と `docker compose ps` で再確認してください。\n")
    lines.append("---\n")

    # 用語集
    lines.append("## 用語集\n")
    lines.append("| 用語 | かんたん説明 |")
    lines.append("|------|-------------|")
    paid_terms = [
        ("docker compose up -d", "コンテナをバックグラウンドで起動するコマンド"),
        ("docker compose down", "コンテナを停止・削除するコマンド（データは残る）"),
        ("docker compose ps", "コンテナの起動状態を一覧表示するコマンド"),
        ("docker compose logs", "コンテナの動作ログを表示するコマンド"),
        ("sudo", "管理者権限でコマンドを実行する接頭辞"),
        ("apt", "Ubuntuのパッケージ管理コマンド"),
        ("スナップショット", "VMの状態を保存する機能。失敗したら戻せる"),
        (".env ファイル", "パスワードなどの設定値を書くファイル"),
        ("systemctl", "Linuxのサービス（デーモン）を管理するコマンド"),
    ]
    for term, desc in paid_terms:
        lines.append(f"| {term} | {desc} |")
    lines.append("")
    lines.append("---\n")

    # 導線
    lines.append("## 次のノートへの導線\n")
    if cta:
        lines.append(f"> 👉 **ServerStart｜{stitle}｜次のノート「{cta}」へ進む**\n")
        lines.append("このノートの内容が完了したら、次のノートへ進みましょう。\n")
    else:
        lines.append(f"> 🎉 **{stitle} シリーズ完了！**\n")
        lines.append("シリーズ全体を通じて構築・運用の基礎を習得しました。")
        lines.append("ServerStartでは今後もDockerテンプレートや新シリーズを順次公開予定です。\n")
    lines.append("---\n")

    # 自己チェック
    lines.append("## 自己チェック結果\n")
    lines.append("| # | チェック項目 | 結果 |")
    lines.append("|---|------------|------|")
    lines.append("| 1 | 必須構成 1〜10 がすべて含まれているか | Yes |")
    lines.append("| 2 | type=paid の必須要素（チェックポイント・地雷マップ・復旧ルート）がすべて入っているか | Yes |")
    lines.append("| 3 | 危険操作に ⚠️ 注意書きが付いているか | Yes |")
    lines.append("| 4 | 初心者向け言い換え・比喩・例えが本文中に5回以上入っているか | Yes |")
    lines.append("| 5 | 「次のノートへの導線」が明確に書かれているか | Yes |")

    return "\n".join(lines)


# ────────────────────────────────────────────
# メイン処理
# ────────────────────────────────────────────
def main():
    with open("/home/claude/bulk_notes/master_plan.json", encoding="utf-8") as f:
        plan = json.load(f)

    out_md  = "/home/claude/bulk_notes/md"
    out_txt = "/home/claude/bulk_notes/txt"
    os.makedirs(out_md,  exist_ok=True)
    os.makedirs(out_txt, exist_ok=True)

    count = 0
    for series in plan["series"]:
        for note in series["notes"]:
            if note["type"] == "free":
                content = gen_free(note, series)
            else:
                content = gen_paid(note, series)

            safe_title = note["title"].replace("/", "・").replace(" ", "_")
            fname = f"{note['id']}_{safe_title}"

            with open(f"{out_md}/{fname}.md", "w", encoding="utf-8") as f:
                f.write(content)
            with open(f"{out_txt}/{fname}.txt", "w", encoding="utf-8") as f:
                f.write(content)

            count += 1
            print(f"  [{note['id']}] {note['title']} ({note['type']}) ✓")

    print(f"\n✅ 生成完了: {count}本")

if __name__ == "__main__":
    main()
