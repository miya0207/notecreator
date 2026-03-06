"""note.com セッションセットアップツール

初回のみ実行が必要です。ブラウザを開いて手動でログインし、
Cookie を保存することで以降の自動投稿が可能になります。

使用方法:
    python tools/setup_note_session.py

    1. ブラウザが起動します（Docker Selenium の場合は VNC でhttp://localhost:7900 を開いてください）
    2. note.com のログインページが表示されます
    3. 手動で Google / X / Apple / メールアドレスでログインしてください
    4. ログイン完了後、このターミナルで Enter を押してください
    5. Cookie が保存されます

注意:
    - Docker Selenium を使用している場合は VNC ビューアが必要です:
      ブラウザで http://localhost:7900 を開く（パスワード: secret）
    - Cookie の有効期限は通常 30 日〜180 日程度です
    - 期限切れ後は再度このツールを実行してください
"""

import os
import sys
import time
from pathlib import Path

# プロジェクトルートをパスに追加
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env", override=False)

from automation.poster.note_client import NoteClient


def main():
    print("=" * 60)
    print("  note.com セッションセットアップ")
    print("=" * 60)
    print()

    remote_url = os.getenv("SELENIUM_REMOTE_URL", "")
    session_file = os.getenv("NOTE_SESSION_FILE", str(_ROOT / ".note_session.json"))

    if remote_url:
        print(f"[設定] Docker Selenium: {remote_url}")
        print()
        print("⚠️  Docker Selenium を使用しています。")
        print("   ブラウザを操作するには VNC ビューアが必要です:")
        print()
        print("   ブラウザで以下を開いてください:")
        print("   http://localhost:7900")
        print("   （パスワード: secret）")
        print()
    else:
        print("[設定] ローカルブラウザ（headless=False で起動）")
        print()

    print(f"[設定] Cookie 保存先: {session_file}")
    print()
    print("準備ができたら Enter を押してブラウザを起動してください...")
    input()

    # headless=False でブラウザを起動（ローカルの場合は画面表示）
    # Docker の場合はリモート接続なので headless 設定は無視される
    client = NoteClient(headless=False, timeout=120)

    try:
        print("[setup] WebDriver を初期化中...")
        client._init_driver()

        print("[setup] note.com ログインページを開いています...")
        client.driver.get("https://note.com/login")
        time.sleep(2)

        print()
        print("=" * 60)
        if remote_url:
            print("  VNC ビューア (http://localhost:7900) でブラウザを操作してください")
        else:
            print("  ブラウザが起動しました。note.com にログインしてください")
        print()
        print("  ログイン方法:")
        print("  - Google / X / Apple ボタン、または")
        print("  - メールアドレスとパスワードでログイン")
        print()
        print("  ログイン完了後（note.com のトップページが表示されたら）")
        print("  このターミナルで Enter を押してください")
        print("=" * 60)
        input()

        # 現在のURLを確認
        current_url = client.driver.current_url
        print(f"\n[setup] 現在のURL: {current_url}")

        if "login" in current_url or "signin" in current_url:
            print("[setup] ⚠️  まだログインページにいます。ログインが完了してから Enter を押してください。")
            print("  もう一度 Enter を押してリトライします...")
            input()
            current_url = client.driver.current_url

        if "note.com" in current_url and "login" not in current_url:
            print("[setup] ✅ ログイン成功を確認！")
            print("[setup] Cookie を保存中...")
            result = client.save_session()
            if result:
                print()
                print("=" * 60)
                print("  ✅ セットアップ完了！")
                print()
                print("  以後は以下のコマンドで自動投稿が可能です:")
                print("  python tools/post_and_generate_threads.py --process-queue")
                print("=" * 60)
            else:
                print("[setup] ❌ Cookie 保存に失敗しました")
        else:
            print(f"[setup] ❌ ログインを確認できませんでした: {current_url}")
            print("  再度実行してください: python tools/setup_note_session.py")

    except KeyboardInterrupt:
        print("\n[setup] キャンセルされました")
    except Exception as e:
        print(f"[setup] エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


if __name__ == "__main__":
    main()
