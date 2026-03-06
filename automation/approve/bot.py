"""Discord承認Botモジュール: Threads投稿案の承認/却下ボタンを処理する。

使用方法:
    python -m automation.approve.bot

必要な環境変数:
    DISCORD_BOT_TOKEN  : BotのToken
    DISCORD_CHANNEL_ID : 対象チャンネルID

## 設計方針

Persistent View (add_view) 方式ではなく on_interaction イベント方式を採用。
理由:
- Persistent View 方式は Bot 起動時に既存 pending の view を登録するため、
  Bot 起動後に送信した新規メッセージのボタンが機能しない。
- on_interaction 方式は custom_id の prefix "approve:" / "reject:" を見て
  record_id を取り出す。Bot の起動タイミングに無関係に全ボタンが機能する。

## 必要な Discord Developer Portal 設定

Privileged Intents は不要。
デフォルト Intents のみで動作する。
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# .env を明示パスで読み込み
_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env", override=False)

try:
    import discord
    from discord.ext import commands
except ImportError:
    print("エラー: discord.py がインストールされていません。")
    print("  pip install discord.py>=2.3.0")
    sys.exit(1)

from automation.approve import store
from automation.poster import queue as post_queue


# -------------------------------------------------------------------------
# 設定
# -------------------------------------------------------------------------

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
CHANNEL_ID_STR = os.getenv("DISCORD_CHANNEL_ID", "")


# -------------------------------------------------------------------------
# 承認処理ヘルパー
# -------------------------------------------------------------------------

async def _handle_decision(
    interaction: discord.Interaction,
    record_id: str,
    status: str,
    label: str,
) -> None:
    """承認/却下の共通処理: ログ更新 + メッセージのボタン無効化"""
    # ① interaction を遅延応答に設定（時間がかかる処理の前に acknowledge）
    await interaction.response.defer(ephemeral=False)

    decided_by = str(interaction.user)
    decided_at = datetime.now().isoformat()

    updated = store.update_status(
        record_id,
        status=status,
        decided_by=decided_by,
        decided_at=decided_at,
    )

    if updated:
        print(
            f"[Bot] {label}: record_id={record_id} "
            f"by={decided_by} at={decided_at}"
        )

        # 承認時：投稿キューに追加
        if status == "approved":
            try:
                # レコードから article_file と tags を取得
                rec = store.find_by_id(record_id)
                if rec and rec.get("article_file"):
                    tags = rec.get("tags", [])
                    post_queue.add_to_queue(record_id, rec.get("article_file"), tags=tags)
                    tag_str = ", ".join(tags) if tags else "なし"
                    print(f"[Bot] ✅ 投稿キューに追加: {record_id} (タグ: {tag_str})")
                else:
                    print(f"[Bot] ⚠️ article_file が見つかりません: {record_id}")
            except Exception as e:
                print(f"[Bot] ⚠️ キュー追加エラー: {e}")

        # ボタンを無効化した View を作成してメッセージを更新
        disabled_view = discord.ui.View()
        disabled_view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.success,
                label="✅ 承認",
                custom_id=f"approve:{record_id}",
                disabled=True,
            )
        )
        disabled_view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.danger,
                label="❌ 却下",
                custom_id=f"reject:{record_id}",
                disabled=True,
            )
        )

        # 承認時の追加メッセージ
        extra_msg = ""
        if status == "approved":
            extra_msg = "\n投稿予約完了: `python tools/post_and_generate_threads.py --process-queue` で投稿してください"

        # ② defer 済みなので edit_original_response() を使用
        await interaction.edit_original_response(
            content=f"{label} — {decided_by} ({decided_at[:10]}){extra_msg}",
            view=disabled_view,
        )
    else:
        print(f"[Bot] 警告: record_id={record_id} のレコードが見つかりません")
        # ③ defer 済みなので followup を使用
        await interaction.followup.send(
            "⚠️ レコードが見つかりませんでした。すでに処理済みか、ログファイルを確認してください。",
            ephemeral=True,
        )


# -------------------------------------------------------------------------
# Bot本体
# -------------------------------------------------------------------------

class ApprovalBot(commands.Bot):
    def __init__(self):
        # message_content は特権インテント (Privileged Intent) のため不要
        # ボタン操作の受付には default intents のみで十分
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        pending_count = len(store.load_pending())
        print(f"[Bot] ログイン完了: {self.user} (id={self.user.id})")
        print(f"[Bot] 現在の承認待ち: {pending_count} 件")
        channel = self.get_channel(int(CHANNEL_ID_STR)) if CHANNEL_ID_STR else None
        if channel:
            print(f"[Bot] 監視チャンネル: #{channel.name} ({CHANNEL_ID_STR})")
        else:
            print(f"[Bot] 警告: DISCORD_CHANNEL_ID={CHANNEL_ID_STR!r} のチャンネルが見つかりません")

    async def on_interaction(self, interaction: discord.Interaction):
        """全インタラクションを受け取り、custom_id prefix で振り分ける。

        approve:{record_id} → 承認
        reject:{record_id}  → 却下
        その他              → デフォルト処理（コマンド等）
        """
        if interaction.type != discord.InteractionType.component:
            await super().on_interaction(interaction)
            return

        custom_id = interaction.data.get("custom_id", "")

        if custom_id.startswith("approve:"):
            record_id = custom_id[len("approve:"):]
            await _handle_decision(interaction, record_id, "approved", "✅ 承認済み")

        elif custom_id.startswith("reject:"):
            record_id = custom_id[len("reject:"):]
            await _handle_decision(interaction, record_id, "rejected", "❌ 却下済み")

        else:
            # 他のコンポーネント（スラッシュコマンド等）はデフォルト処理に委譲
            await super().on_interaction(interaction)


def run():
    """Botを起動する"""
    if not BOT_TOKEN:
        print("エラー: DISCORD_BOT_TOKEN が設定されていません")
        print("  .env に DISCORD_BOT_TOKEN=your-token を設定してください")
        sys.exit(1)

    if not CHANNEL_ID_STR:
        print("警告: DISCORD_CHANNEL_ID が設定されていません")

    bot = ApprovalBot()
    print("[Bot] 起動中...")
    bot.run(BOT_TOKEN)


if __name__ == "__main__":
    run()
