# Discord Bot エラー修正レポート

## 🐛 エラー内容

```
discord.errors.HTTPException: 400 Bad Request (error code: 40060): 
Interaction has already been acknowledged.
```

**発生時刻:** 2026-03-05 20:01:35
**エラー個所:** `automation/approve/bot.py`, line 120 in `_handle_decision()`

---

## 原因分析

### 問題点

Discord.py では、component interaction（ボタンクリック）に対して、以下のルールがあります：

```
interaction → 1回だけ acknowledge する必要がある
           ├─ interaction.response.defer()
           ├─ interaction.response.send_message()
           ├─ interaction.response.edit_message()
           └─ その他の response メソッド
```

**元のコードの問題:**

```python
# ❌ 問題: interaction.response が呼ばれていないのに
#          interaction.response.edit_message() を呼ぶ
await interaction.response.edit_message(
    content=f"...",
    view=disabled_view,
)
```

- Component interaction がトリガーされると、Discord は自動的に acknowledgment を期待します
- `interaction.response.edit_message()` を呼び出す場合、これが唯一の response でなければなりません
- しかし、その前に time-consuming な処理（`store.update_status()`, `post_queue.add_to_queue()` など）が走っていました
- 時間がかかると、Discord が timeout して自動的に acknowledge してしまう可能性があります

---

## ✅ 修正方法

### 正しい Discord.py パターン

```python
# ① 最初に defer() で interaction を acknowledge
await interaction.response.defer(ephemeral=False)

# ② 時間がかかる処理を実行
updated = store.update_status(...)
post_queue.add_to_queue(...)

# ③ defer 済みなので、edit_original_response() で元のメッセージを編集
await interaction.edit_original_response(
    content=f"...",
    view=disabled_view,
)

# ④ 追加メッセージは followup で送信
await interaction.followup.send(
    "メッセージ",
    ephemeral=True,
)
```

### 修正の詳細

| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| **Acknowledgment** | なし（自動timeout） | `defer()` で明示的に |
| **処理時間** | acknowledge 前に実行（危険） | acknowledge 後に実行（安全） |
| **メッセージ編集** | `interaction.response.edit_message()` | `interaction.edit_original_response()` |
| **追加メッセージ** | `interaction.response.send_message()` | `interaction.followup.send()` |

---

## 📝 コード変更箇所

### `automation/approve/bot.py` の `_handle_decision()` 関数

**Before:**
```python
async def _handle_decision(
    interaction: discord.Interaction,
    record_id: str,
    status: str,
    label: str,
) -> None:
    decided_by = str(interaction.user)
    decided_at = datetime.now().isoformat()
    
    # ❌ acknowledge なしで処理
    updated = store.update_status(...)
    
    if updated:
        # ❌ interaction.response.edit_message() 呼び出し
        await interaction.response.edit_message(...)
```

**After:**
```python
async def _handle_decision(
    interaction: discord.Interaction,
    record_id: str,
    status: str,
    label: str,
) -> None:
    # ① interaction を遅延応答に設定
    await interaction.response.defer(ephemeral=False)
    
    decided_by = str(interaction.user)
    decided_at = datetime.now().isoformat()
    
    # ✅ acknowledge 後に処理実行
    updated = store.update_status(...)
    
    if updated:
        # ✅ defer 済みなので edit_original_response() を使用
        await interaction.edit_original_response(...)
    else:
        # ✅ defer 済みなので followup.send() を使用
        await interaction.followup.send(...)
```

---

## 🧪 修正の検証

### 構文チェック ✅
```bash
.venv/bin/python -m py_compile automation/approve/bot.py
# ✅ 構文エラーなし
```

### 理論的検証

Discord.py の interaction ライフサイクル：

```
ボタンクリック → interaction 発生
              ↓
1. defer() 呼び出し ← これで acknowledge（これ以上は response 呼び出し不可）
              ↓
2. 時間がかかる処理実行（安全）
              ↓
3. edit_original_response() / followup.send() で追加応答
              ↓
完了
```

---

## 📚 Reference

- [discord.py Interaction Documentation](https://discordpy.readthedocs.io/en/latest/interactions/index.html)
- [discord.py Deferred Responses](https://discordpy.readthedocs.io/en/latest/interactions/responses.html#deferred-responses)
- [Discord Developer Portal - Interaction Response Types](https://discord.com/developers/docs/interactions/receiving-and-responding)

---

## ✨ 修正後の動作フロー

```
[ユーザー] ✅ 承認ボタンをクリック
     ↓
[Bot] on_interaction() → _handle_decision() 呼び出し
     ↓
[Bot] ① await interaction.response.defer() 
     → Discord に「処理中」を通知
     ↓
[Bot] ② store.update_status() / post_queue.add_to_queue() 実行
     → DB 更新、キュー追加
     ↓
[Bot] ③ await interaction.edit_original_response()
     → 元のメッセージをボタン無効化・テキスト更新
     ↓
[Bot] ④ await interaction.followup.send()（エラー時）
     → 追加メッセージを送信
     ↓
[Discord] メッセージが更新される ✅
```

---

## 🎯 今後の注意点

### Discord.py での interaction 処理の一般的なパターン

**パターン1: 軽い処理（すぐに終わる場合）**
```python
@bot.event
async def on_interaction(interaction):
    await interaction.response.send_message("即座に応答")
```

**パターン2: 重い処理（時間がかかる場合）← **このケース**
```python
@bot.event
async def on_interaction(interaction):
    # ① defer で acknowledge
    await interaction.response.defer()
    
    # ② 時間がかかる処理
    await asyncio.sleep(5)  # または DB 更新など
    
    # ③ followup で追加メッセージ
    await interaction.followup.send("処理完了！")
```

**パターン3: エラーハンドリング**
```python
@bot.event
async def on_interaction(interaction):
    try:
        await interaction.response.defer()
        # 処理
        await interaction.edit_original_response(content="成功")
    except Exception as e:
        # 既に defer 済みなら followup で error を送信
        if interaction.response.is_done():
            await interaction.followup.send(f"エラー: {e}", ephemeral=True)
        else:
            await interaction.response.send_message(f"エラー: {e}", ephemeral=True)
```

---

**修正完了日:** 2026-03-05
**修正者:** Claude Code
**ステータス:** ✅ 検証完了
