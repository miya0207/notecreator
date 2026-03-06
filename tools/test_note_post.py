#!/usr/bin/env python3
"""
note.com 疎通確認テスト
ダミーデータでnoteに直接投稿し、全体フローを検証する

使い方:
    python tools/test_note_post.py
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env", override=False)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ──────────────────────────────────────────
#  テスト用ダミーデータ
# ──────────────────────────────────────────
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")

TEST_TITLE = f"【自動投稿テスト】Playwright疎通確認 ({NOW})"

TEST_CONTENT = """# Playwright自動投稿 — 疎通確認テスト

このノートは自動投稿システムの動作確認として作成されました。

## テスト目的

- note.com へのログインが正常に機能していることを確認
- 記事投稿フロー（タイトル入力→本文入力→公開）の検証
- 投稿後のURL取得が正常に動作していることを確認

## テスト環境

- 自動化ツール: Selenium + Docker Chrome
- 実行日時: {now}
- テスト種別: 疎通確認（ダミーデータ）

## 結果

このテストが正常に表示されている場合、自動投稿システムは正常に機能しています ✅

---
*このノートはシステムテスト目的で作成されました。*
""".format(now=NOW)

# ──────────────────────────────────────────
#  設定
# ──────────────────────────────────────────
REMOTE_URL = os.getenv("SELENIUM_REMOTE_URL", "http://localhost:4444/wd/hub")
MAIL_ADDRESS = os.getenv("NOTE_MAIL_ADDRESS", "")
MAIL_PASSWORD = os.getenv("NOTE_MAIL_PASSWORD", "")
TIMEOUT = 30
SS_DIR = _ROOT / "out"
SS_DIR.mkdir(exist_ok=True)


def save_ss(driver, name: str):
    """スクリーンショット保存（デバッグ用）"""
    path = SS_DIR / f"test_{name}.png"
    driver.save_screenshot(str(path))
    print(f"  📸 SS: {path.name}")


def init_driver():
    """Docker Seleniumに接続"""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    print(f"[1/6] Docker Selenium ({REMOTE_URL}) に接続中...")
    driver = webdriver.Remote(command_executor=REMOTE_URL, options=options)
    driver.implicitly_wait(10)
    print("  ✅ 接続成功")
    return driver


def do_login(driver):
    """ログイン処理"""
    print("[2/6] note.com にログイン中...")
    driver.get("https://note.com/login")
    time.sleep(3)
    save_ss(driver, "01_login_page")

    wait = WebDriverWait(driver, TIMEOUT)

    # 全inputを取得
    inputs = wait.until(lambda d: d.find_elements(By.TAG_NAME, "input"))
    print(f"  入力フィールド: {len(inputs)}個")
    if len(inputs) < 2:
        raise Exception(f"フィールド不足: {len(inputs)}個")

    # メールアドレス
    inputs[0].click()
    time.sleep(0.3)
    inputs[0].send_keys(MAIL_ADDRESS)
    time.sleep(0.5)

    # パスワード
    inputs[1].click()
    time.sleep(0.3)
    inputs[1].send_keys(MAIL_PASSWORD)
    time.sleep(0.5)

    save_ss(driver, "02_filled_login")

    # ログインボタンクリック
    try:
        login_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'ログイン') and not(@disabled)]")
            )
        )
        login_btn.click()
    except Exception:
        # disabledでもJSで強制クリック
        btn = driver.find_element(By.XPATH, "//button[contains(., 'ログイン')]")
        driver.execute_script("arguments[0].click();", btn)

    time.sleep(5)
    current = driver.current_url
    save_ss(driver, "03_after_login")

    if "login" in current or "signin" in current:
        raise Exception(f"ログイン失敗 — URL: {current}")

    print(f"  ✅ ログイン成功: {current}")
    return True


def open_editor(driver):
    """新規記事エディタを開く"""
    print("[3/6] 新規記事エディタを開く...")

    # note エディタURL候補
    editor_urls = [
        "https://note.com/notes/new",
        "https://editor.note.com/new",
    ]

    for url in editor_urls:
        driver.get(url)
        time.sleep(4)
        current = driver.current_url
        if "login" not in current and "signin" not in current:
            print(f"  ✅ エディタURL: {current}")
            save_ss(driver, "04_editor_opened")
            return
        print(f"  ⚠️ リダイレクト: {current}")

    # どちらもダメなら現在のURLで続行
    save_ss(driver, "04_editor_opened")
    print(f"  現在URL: {driver.current_url}")


def enter_title(driver):
    """タイトル入力"""
    print("[4/6] タイトルを入力中...")
    wait = WebDriverWait(driver, TIMEOUT)

    # タイトル候補セレクタ
    title_selectors = [
        (By.CSS_SELECTOR, "input[data-placeholder*='タイトル']"),
        (By.CSS_SELECTOR, "textarea[placeholder*='タイトル']"),
        (By.CSS_SELECTOR, "input[placeholder*='タイトル']"),
        (By.XPATH, "//input[contains(@placeholder,'タイトル')]"),
        (By.XPATH, "//textarea[contains(@placeholder,'タイトル')]"),
    ]

    title_el = None
    for by, sel in title_selectors:
        try:
            title_el = wait.until(EC.element_to_be_clickable((by, sel)))
            print(f"  ✅ タイトルフィールド発見: {sel}")
            break
        except Exception:
            continue

    # 候補が全て失敗した場合: contenteditable要素で試みる
    if title_el is None:
        try:
            content_editables = driver.find_elements(
                By.CSS_SELECTOR, "[contenteditable='true']"
            )
            if content_editables:
                title_el = content_editables[0]
                print(f"  ✅ contenteditable要素で代替: {len(content_editables)}個中1番目")
        except Exception:
            pass

    if title_el is None:
        save_ss(driver, "04b_title_field_failed")
        raise Exception("タイトルフィールドが見つかりません")

    title_el.click()
    time.sleep(0.5)
    # 既存テキストをクリア
    title_el.send_keys(Keys.CONTROL + "a")
    time.sleep(0.2)
    title_el.send_keys(TEST_TITLE)
    time.sleep(1)

    save_ss(driver, "05_title_entered")
    print(f"  ✅ タイトル入力完了: {TEST_TITLE[:40]}...")


def enter_content(driver):
    """本文入力"""
    print("[5/6] 本文を入力中...")
    wait = WebDriverWait(driver, TIMEOUT)

    # 本文フィールド候補セレクタ
    content_selectors = [
        (By.CSS_SELECTOR, ".note-body [contenteditable='true']"),
        (By.CSS_SELECTOR, "[data-editor] [contenteditable='true']"),
        (By.CSS_SELECTOR, ".ProseMirror"),
        (By.CSS_SELECTOR, "[role='textbox']"),
    ]

    content_el = None
    for by, sel in content_selectors:
        try:
            content_el = wait.until(EC.element_to_be_clickable((by, sel)))
            print(f"  ✅ 本文フィールド発見: {sel}")
            break
        except Exception:
            continue

    # 候補が全て失敗: contenteditable要素の2番目
    if content_el is None:
        try:
            content_editables = driver.find_elements(
                By.CSS_SELECTOR, "[contenteditable='true']"
            )
            if len(content_editables) >= 2:
                content_el = content_editables[1]
                print(f"  ✅ contenteditable要素で代替: 2番目を使用")
            elif content_editables:
                # Tabキーで次フィールドに移動
                content_editables[0].send_keys(Keys.TAB)
                time.sleep(0.5)
                content_el = driver.switch_to.active_element
                print("  ✅ Tabキーで次フィールドに移動")
        except Exception:
            pass

    if content_el is None:
        save_ss(driver, "05b_content_field_failed")
        raise Exception("本文フィールドが見つかりません")

    content_el.click()
    time.sleep(0.5)

    # 本文を行ごとに入力（長文の一括送信は失敗しやすいため）
    lines = TEST_CONTENT.split("\n")
    for i, line in enumerate(lines):
        content_el.send_keys(line)
        if i < len(lines) - 1:
            content_el.send_keys(Keys.SHIFT + Keys.ENTER)
        time.sleep(0.05)

    time.sleep(2)
    save_ss(driver, "06_content_entered")
    print(f"  ✅ 本文入力完了 ({len(TEST_CONTENT)}文字)")


def publish_article(driver):
    """記事を公開する (2ステップ: 公開に進む → 公開する)"""
    print("[6/6] 記事を公開中...")
    wait = WebDriverWait(driver, TIMEOUT)

    # ── Step A: 「公開に進む」ボタン ──────────────────
    print("  Step A: 「公開に進む」ボタンを探す...")
    save_ss(driver, "07_before_publish_btn")

    step_a_selectors = [
        (By.XPATH, "//button[contains(text(),'公開に進む')]"),
        (By.XPATH, "//button[normalize-space()='公開に進む']"),
        (By.CSS_SELECTOR, "button[data-testid*='publish']"),
        (By.XPATH, "//button[contains(.,'公開')]"),
    ]

    next_btn = None
    for by, sel in step_a_selectors:
        try:
            next_btn = wait.until(EC.element_to_be_clickable((by, sel)))
            print(f"  ✅ 「公開に進む」発見: {sel}")
            break
        except Exception:
            continue

    if next_btn is None:
        # 全ボタンをリストして確認
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        btn_texts = [b.text for b in all_buttons if b.text.strip()]
        print(f"  利用可能なボタン: {btn_texts}")
        save_ss(driver, "07b_all_buttons")
        raise Exception("「公開に進む」ボタンが見つかりません")

    next_btn.click()
    time.sleep(4)
    save_ss(driver, "08_publish_settings_page")
    print(f"  ✅ 公開設定ページ遷移: {driver.current_url}")

    # ── Step B: 「公開する」/「投稿する」ボタン ──────
    print("  Step B: 「公開する」ボタンを探す...")

    step_b_selectors = [
        (By.XPATH, "//button[normalize-space()='公開する']"),
        (By.XPATH, "//button[normalize-space()='投稿する']"),
        (By.XPATH, "//button[contains(text(),'公開する')]"),
        (By.XPATH, "//button[contains(text(),'投稿')]"),
        (By.CSS_SELECTOR, "button[data-testid*='confirm']"),
        (By.CSS_SELECTOR, "button[data-testid*='submit']"),
    ]

    publish_btn = None
    for by, sel in step_b_selectors:
        try:
            publish_btn = wait.until(EC.element_to_be_clickable((by, sel)))
            print(f"  ✅ 「公開する」発見: {sel}")
            break
        except Exception:
            continue

    if publish_btn is None:
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        btn_texts = [f"'{b.text}'" for b in all_buttons if b.text.strip()]
        print(f"  利用可能なボタン: {btn_texts}")
        save_ss(driver, "09b_publish_btn_failed")
        raise Exception("「公開する」ボタンが見つかりません")

    publish_btn.click()
    print("  ✅ 公開ボタンをクリック")
    time.sleep(5)
    save_ss(driver, "09_after_publish")


def get_article_url(driver):
    """投稿後のURL取得"""
    wait = WebDriverWait(driver, TIMEOUT)
    current = driver.current_url
    print(f"  現在URL: {current}")

    # URLに /n/ が含まれていれば成功
    if "/n/" in current and "new" not in current:
        return current

    # リダイレクト待機
    try:
        wait.until(lambda d: "/n/" in d.current_url)
        return driver.current_url
    except Exception:
        pass

    # フォールバック: マイページから最新記事を取得
    print("  フォールバック: マイページから最新記事URLを取得...")
    driver.get("https://note.com/my/contributions")
    time.sleep(3)
    try:
        link = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@href, '/n/')]")
            )
        )
        return link.get_attribute("href")
    except Exception:
        return None


# ──────────────────────────────────────────
#  メイン処理
# ──────────────────────────────────────────
def main():
    print("=" * 60)
    print("  note.com 疎通確認テスト")
    print(f"  実行日時: {NOW}")
    print("=" * 60)

    # 認証情報確認
    if not MAIL_ADDRESS or not MAIL_PASSWORD:
        print("❌ 環境変数 NOTE_MAIL_ADDRESS / NOTE_MAIL_PASSWORD が未設定")
        sys.exit(1)

    print(f"\n📝 テスト記事情報:")
    print(f"  タイトル: {TEST_TITLE}")
    print(f"  本文文字数: {len(TEST_CONTENT)}文字")
    print(f"\n📡 接続先: {REMOTE_URL}")
    print(f"👤 ログイン: {MAIL_ADDRESS[:5]}***\n")

    driver = None
    try:
        driver = init_driver()
        do_login(driver)
        open_editor(driver)
        enter_title(driver)
        enter_content(driver)
        publish_article(driver)

        article_url = get_article_url(driver)
        save_ss(driver, "10_final")

        print("\n" + "=" * 60)
        if article_url:
            print(f"  ✅ 投稿成功！")
            print(f"  記事URL: {article_url}")
        else:
            print(f"  ⚠️ 投稿完了（URL取得失敗）")
            print(f"  現在URL: {driver.current_url}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        if driver:
            save_ss(driver, "99_error")
        raise

    finally:
        if driver:
            driver.quit()
            print("\n🔒 ブラウザセッションを終了しました")


if __name__ == "__main__":
    main()
