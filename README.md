# notecreator

ServerStart ノート生成・管理用リポジトリ。

このリポジトリは、
**初心者向けサーバー／Linux／Docker 学習ノート（全29本）**を
設計・生成・管理するための基盤です。

加えて、**AI記事工場**（SEOトレンド収集＋記事自動生成＋収益導線）を搭載しています。

---

## 📚 ノート一覧（まずここを見る）
- 👉 [全ノートINDEX（29本）](./final_package/INDEX.md)

無料ノート／有料ノートの区分、シリーズ構成は
すべて INDEX にまとまっています。

---

## 🧠 設計思想
- 初心者の「怖い・分からない」を先に潰す
- 無料＝概念理解／不安解消
- 有料＝手順・コマンド・地雷マップ・復旧ルート
- 失敗前提で安全に戻れる設計

---

## 🤖 AI記事工場

「AI × IT初心者」ジャンルのnoteアフィリエイト自動化パイプラインです。

### 4つのAIシステム

| # | システム | 説明 | 出力先 |
|---|---------|------|--------|
| ① | SEOトレンド収集AI | HackerNews/Reddit/Qiita/Zennからトレンド収集＋スコアリング | `out/trends/` |
| ② | AI記事工場 | Claude APIでnote記事を自動生成（プレーンテキスト） | `out/articles/` |
| ③ | アフィリエイト最適化AI | 記事テーマに最適な広告候補＋A8キーワード生成 | `out/affiliate/` |
| ④ | note収益導線AI | 有料note企画（タイトル/目次/価格案）を生成 | `out/premium/` |

+ Threads投稿生成 → `out/threads/`
+ 自動品質検査 → `out/reports/`

### セットアップ

```bash
# 依存パッケージインストール
pip install -r requirements.txt

# APIキー設定
cp .env.example .env
# .env を編集して ANTHROPIC_API_KEY を設定
```

### 実行方法

```bash
# 全パイプライン実行（SEO収集→記事生成→広告→有料note→Threads→検査）
python run_auto.py

# トレンド収集のみ
python run_auto.py --trends-only

# 記事生成のみ（既存トレンド使用）
python run_auto.py --articles-only

# 生成記事数を指定（デフォルト3本）
python run_auto.py --count 5

# テスト実行（API呼び出しなし）
python run_auto.py --dry-run
```

### 運用方法

毎日の運用フロー:
1. `python run_auto.py` で1〜3本の記事を自動生成
2. `out/articles/` の記事を確認・微修正
3. noteに投稿
4. `out/threads/` のテキストをThreadsに投稿
5. `out/affiliate/` の広告候補を参考にA8リンクを挿入
6. `out/premium/` の企画を参考に有料noteを作成

---

## 🛠 ディレクトリ構成
```
final_package/          # ServerStart 29本ノート生成（既存）
├─ INDEX.md
├─ master_plan.json
├─ generate_all.py
├─ build_prompts.py
├─ 03_全29本_本文_md/
└─ 04_全29本_本文_txt/

run_auto.py             # AI記事工場メインコマンド
config/
├─ topics.yml           # トピック・ジャンル設定
└─ affiliate.yml        # 広告カテゴリ設定
automation/
├─ common/              # 共通基盤（設定/Claude API）
├─ trends/              # ① SEOトレンド収集
├─ articles/            # ② 記事生成＋フォーマッター
├─ affiliate/           # ③ アフィリエイト最適化
├─ premium/             # ④ 有料note企画
├─ threads/             # Threads投稿生成
└─ quality/             # 自動品質検査
out/                    # 全出力先（Git管理外）
```

---

## ⚠️ 注意
- .env / 鍵 / トークン類は Git 管理しない
- `out/` ディレクトリは `.gitignore` で除外済み
- 本リポジトリは生成・管理用
