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

| # | システム | 使用モデル | 説明 | 出力先 |
|---|---------|----------|------|--------|
| ① | SEOトレンド収集AI | FAST | HackerNews/Reddit/Qiita/Zennからトレンド収集＋スコアリング | `out/trends/` |
| ② | AI記事工場 | ARTICLE | Claude APIでnote記事を自動生成（プレーンテキスト・1200文字以上） | `out/articles/` |
| ③ | アフィリエイト最適化AI | FAST | 記事テーマに最適な広告候補＋A8キーワード生成 | `out/affiliate/` |
| ④ | note収益導線AI | FAST | 有料note企画（タイトル/目次/価格案）を生成 | `out/premium/` |

+ Threads投稿生成（FAST）→ `out/threads/`
+ 自動品質検査（ローカル）→ `out/reports/`

### セットアップ

```bash
# 1. 仮想環境を有効化（初回はvenv作成が必要）
source .venv/bin/activate   # または: python3 -m venv .venv && source .venv/bin/activate

# 2. 依存パッケージインストール
pip install -r requirements.txt

# 3. APIキー設定
cp .env.example .env
nano .env   # ANTHROPIC_API_KEY を設定
```

### .env 設定例

```dotenv
ANTHROPIC_API_KEY=sk-ant-xxxxx        # 必須: Anthropic APIキー

CLAUDE_MODEL_ARTICLE=claude-sonnet-4-6          # 記事生成（高品質）
CLAUDE_MODEL_FAST=claude-haiku-4-5-20251001     # 軽量処理（高速・低コスト）
CLAUDE_MODEL=claude-sonnet-4-6                  # フォールバック
```

**モデル切替**: `.env` の値を変えるだけでOK。コードの変更は不要。

### 実行方法

```bash
# 動作確認（API呼び出しなし・全件PASSを確認）
python run_auto.py --dry-run --count 3

# 本番実行（全パイプライン: SEO収集→記事生成→広告→有料note→Threads→検査）
python run_auto.py --count 1   # 1本
python run_auto.py --count 3   # 3本（デフォルト）

# 部分実行
python run_auto.py --trends-only      # トレンド収集のみ
python run_auto.py --articles-only    # 記事生成のみ（既存トレンド使用）
```

### 記事品質検査（6項目）

| 検査項目 | 基準 |
|---------|------|
| PR表記 | 冒頭に「※本記事には広告が含まれます」 |
| 広告枠 | `{{A8_LINK_TOP/MID/BOTTOM}}` 各1箇所 |
| 文字数 | 1200文字以上 |
| NG表現 | 誇大広告ワードなし |
| プレーンテキスト | Markdown/HTMLなし |
| テンプレート準拠 | 必須セクション全て存在 |

### 毎日の運用フロー

```
python run_auto.py --count 3
   ↓
out/articles/ の記事を確認・A8リンクを挿入
   ↓
note に投稿
   ↓
out/threads/ のテキストを Threads に投稿
   ↓
out/premium/ の企画を参考に有料note作成
```

### トラブルシューティング

| エラー | 対処 |
|-------|------|
| `model: xxxx not found` | `.env` の `CLAUDE_MODEL_*` を確認 |
| `ANTHROPIC_API_KEY が設定されていません` | `.env` にAPIキーを設定 |
| 記事が短い（1200文字未満）| APIを再実行 or プロンプトを調整 |
| 検査FAIL | `out/reports/` のJSONで原因確認 |

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
