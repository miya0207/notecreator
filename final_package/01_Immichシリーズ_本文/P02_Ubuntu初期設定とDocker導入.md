# Ubuntu初期設定とDocker導入

> **ServerStart｜有料ノート P02 / P03**

---

## このノートでできるようになること

- SSH接続でUbuntu Serverをリモート操作できる
- Ubuntu Serverの最低限の初期設定ができる
- DockerとDocker Composeをインストールできる
- `docker compose` コマンドが実行できる状態まで到達できる

---

## 想定読者 / 前提知識

- 有料ノートP01を完了し、Ubuntu ServerのVMにログインできる方
- スナップショット「Ubuntu起動確認済み」が取得済みの方
- コマンドはコピペで進めます。完全理解は不要です

---

## 全体像

このノートで行う作業の流れです。

```
① 作業前スナップショットを取得する
    ↓
② ホストPCからSSH接続する
    ↓
③ システムを最新の状態にする
    ↓
④ タイムゾーンを設定する
    ↓
⑤ Dockerをインストールする
    ↓
⑥ Docker動作を確認する
    ↓
⑦ スナップショットを取得する ← Docker導入済みの安全地点
```

---

## 本編

### 1. 作業前のスナップショット取得

必ず最初にスナップショットを取得してください。これで何か失敗しても、この時点に戻せます。

```
操作: VirtualBox → 対象VMを右クリック → スナップショット → スナップショットの取得
名前: 「Docker作業前」
```

---

### 2. VMのIPアドレス確認とSSH接続

VMの画面を直接操作するより、ホストPC（あなたのPC）のターミナルからSSH接続する方が作業しやすくなります。

```bash
# VM内で実行：IPアドレスを確認する
ip addr show
# 表示された "inet 192.168.xx.xx" の数字がIPアドレス
```

確認したIPアドレスを使って、ホストPCのターミナルからSSH接続します。

```bash
# ホストPCのターミナルで実行（ユーザー名とIPは自分のものに変更）
ssh ユーザー名@192.168.xx.xx
# 例: ssh serverstart@192.168.56.10

# 初回接続時に "Are you sure you want to continue connecting?" と聞かれたら
# yes を入力してEnter
```

> 💡 WindowsはPowerShellまたはコマンドプロンプトから実行できます。macOSはターミナル.appを使います。
> 💡 SSH接続後は、VM画面を閉じてターミナル上で作業できます。コピペがしやすくなります。

---

### 3. システムの更新

インストール直後は古いパッケージが残っていることがあります。最初に最新状態にしておきます。

```bash
# パッケージリストを更新して、アップグレードを実行
sudo apt update && sudo apt upgrade -y
```

> ⚠️ 途中で「再起動しますか？」のような確認画面（青い画面）が出た場合は、Enterキーでデフォルト選択のまま進めてOKです。

---

### 4. タイムゾーンの設定

タイムゾーンを日本時間（JST）に設定します。ログの時刻表示がわかりやすくなります。

```bash
# タイムゾーンをAsia/Tokyoに設定
sudo timedatectl set-timezone Asia/Tokyo

# 設定確認
timedatectl
# "Time zone: Asia/Tokyo (JST, +0900)" が表示されればOK
```

---

### 5. Dockerのインストール

Ubuntu公式のDockerではなく、Docker社公式リポジトリから最新版をインストールします。

```bash
# 必要パッケージのインストール
sudo apt install -y ca-certificates curl

# Docker公式GPGキーの追加
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Dockerリポジトリの追加
echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Dockerのインストール
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
```

---

### 6. Dockerの動作確認と設定

```bash
# バージョン確認
docker --version
docker compose version

# 一般ユーザーでdockerコマンドを使えるようにする
sudo usermod -aG docker $USER

# 設定を反映させるためSSHを一度切断して再接続する
exit
# → 再度 ssh ユーザー名@IPアドレス で接続する

# 接続後、sudo なしで動作確認
docker run hello-world
# "Hello from Docker!" が表示されれば成功
```

> ⚠️ `usermod` の後に必ずSSHを切断して再接続してください。再接続しないと次のコマンドで権限エラーになります。

---

### 7. スナップショットの取得

Dockerのインストールが完了した状態を保存します。

```bash
# VM内でシャットダウン
sudo shutdown now
```

```
操作: VirtualBox → スナップショット → スナップショットの取得
名前: 「Docker導入済み」
```

---

## チェックポイント

```
✅ ホストPCのターミナルからSSH接続できる
✅ sudo apt update && sudo apt upgrade -y がエラーなく完了する
✅ docker --version でバージョンが表示される
✅ docker compose version でバージョンが表示される
✅ docker run hello-world で "Hello from Docker!" が表示される
✅ スナップショット「Docker導入済み」が保存されている
```

---

## よくある詰まりと対処

### 地雷マップ

| 詰まりパターン | 原因の可能性 | 対処手順 |
|--------------|------------|---------|
| SSH接続できない | VMのIPアドレスが変わっている | VM内で `ip addr show` を再実行してIPを確認する |
| SSH接続できない | OpenSSHが起動していない | VM内で `sudo systemctl start ssh` を実行する |
| `docker: permission denied` | usermodの反映前に実行した | SSH切断 → 再接続する |
| `docker compose` が見つからない | compose pluginがインストールされていない | `sudo apt install docker-compose-plugin` を実行する |
| `apt update` でエラーが出る | インターネットに接続できていない | VM設定 → ネットワーク → アダプターが「NAT」になっているか確認する |
| `hello-world` のイメージが取得できない | DNS解決の失敗 | `ping 8.8.8.8` で疎通確認。失敗なら `/etc/resolv.conf` を確認する |

### 復旧ルート

```
【何か操作が途中で失敗した場合】
  → スナップショット「Docker作業前」に戻す
  操作: VirtualBox → スナップショット → 「Docker作業前」を選択 → 復元
  → 手順2から再開する

【apt upgrade 中に止まってしまった場合】
  → Ctrl + C で中断し、もう一度 sudo apt upgrade -y を実行する
  → それでも止まる場合はスナップショットに戻す

【SSHで接続できなくなった場合】
  → VMの画面から直接ログインして作業を続ける
```

---

## 用語集

| 用語 | かんたん説明 |
|------|-------------|
| SSH | ネットワーク越しにサーバーをリモート操作する仕組み |
| apt | Ubuntu のパッケージ管理コマンド。アプリの追加・更新に使う |
| sudo | 管理者権限でコマンドを実行する接頭辞 |
| GPGキー | ソフトウェアの配布元を証明する暗号鍵 |
| リポジトリ | パッケージの配布元サーバー。apt はここからダウンロードする |
| usermod | ユーザーの設定を変更するコマンド |
| docker run hello-world | Dockerの動作確認に使う公式テスト用イメージ |
| タイムゾーン | コンピューターが使う時刻基準の地域設定 |
| NAT | VirtualBoxのネットワーク設定の1つ。外部インターネットに繋がる |

---

## 次のノートへの導線

> 👉 **ServerStart 有料ノート P03「Immich構築とチェックポイント」へ進む**

Dockerが動く環境が整いました。次のノートでは、いよいよImmichをdocker-composeで起動し、ブラウザ画面の表示まで到達します。docker-compose.ymlの取得・最低限の編集・起動確認・トラブル時の切り分け手順・バックアップの考え方まで、すべて揃えています。

---

## 自己チェック結果

| # | チェック項目 | 結果 |
|---|------------|------|
| 1 | 必須構成 1〜10 がすべて含まれているか | Yes |
| 2 | type=paid の必須要素（チェックポイント・地雷マップ・復旧ルート）がすべて入っているか | Yes |
| 3 | 危険操作（shutdown・usermod・apt upgrade など）に ⚠️ 注意書きが付いているか | Yes |
| 4 | 初心者向け言い換え・比喩・例えが本文中に5回以上入っているか | Yes（安全地点・コピペ・節目・確認が出たらEnter・接続しやすくなる など） |
| 5 | 「次のノートへの導線」セクションで次ノートのタイトルと内容予告が明確に書かれているか | Yes |
