# リマインダー

日々のタスクと「今日のメモ」を管理する、Windows向けのデスクトップアプリです。
要件は [docs/requirements.md](docs/requirements.md) を参照してください。

## アプリを使う（exe）

Python がなくても、exe をダウンロードすればどの Windows PC でも実行できます。

1. GitHub の [Releases](https://github.com/SeijiFukuhara/reminder/releases) を開く
2. 最新版の `Reminder.exe` をダウンロードする
3. 好きな場所（例: デスクトップ、`C:\Apps`）に置いて、ダブルクリックで起動する

> 初回起動時に「Windows によって PC が保護されました」と表示された場合は、
> 「詳細情報」→「実行」を押してください（署名のない自作アプリのため表示されます）。

### データの保存場所

タスクとメモは `%APPDATA%\ReminderApp\data.json` に自動で保存されます。
exe を置き換えて（更新して）もデータは消えません。
別の PC にデータを移したいときは、このファイルをコピーしてください。

## 自分で exe を作る

### ZIP ファイルから作る（git がなくてもできます）

#### 1. Python をインストールする（初回のみ）

1. [python.org](https://www.python.org/downloads/) から Windows 用の Python（3.10 以上）をダウンロードする
2. インストーラーの最初の画面で **「Add python.exe to PATH」にチェックを入れて**から「Install Now」を押す

インストールできたかは、コマンドプロンプトで `python --version` と入力して、バージョンが表示されれば OK です。

#### 2. コードを ZIP でダウンロードして展開する

1. [リポジトリのページ](https://github.com/SeijiFukuhara/reminder) を開く
2. 緑色の「**Code**」ボタン →「**Download ZIP**」を押す
3. ダウンロードした `reminder-main.zip` を右クリック →「**すべて展開**」を押す
   - 展開先は `C:\Users\<ユーザー名>\reminder-main` などの分かりやすい場所にする
   - ZIP を開いただけ（展開せずに中を見ている状態）では実行できないので、必ず展開してください

#### 3. exe を作る

1. 展開したフォルダ（`main.py` や `build.bat` が入っているフォルダ）を開く
2. `build.bat` をダブルクリックする
   - 「Windows によって PC が保護されました」と表示されたら、「詳細情報」→「実行」を押す
3. 黒い画面で処理が進むので、1〜3分ほど待つ
4. `Done: ...\dist\Reminder.exe` と表示されたら完成。何かキーを押して画面を閉じる

#### 4. exe を実行する

1. フォルダ内にできた `dist` フォルダを開く
2. `Reminder.exe` をダブルクリックして起動する

`Reminder.exe` はこれ1つで動くので、デスクトップなど好きな場所にコピーして使えます
（コピーした後は、展開したフォルダを消してもかまいません）。

#### うまくいかないとき

| 表示 | 対処 |
|------|------|
| `Python was not found.` | Python が入っていないか、「Add python.exe to PATH」にチェックせずにインストールしています。手順 1 をやり直してください |
| `Build failed.` | インターネットに接続されているか確認してから、もう一度 `build.bat` を実行してください |
| `build.bat` がすぐ閉じる | ZIP を展開せずに開いている可能性があります。手順 2 の「すべて展開」を行ってください |

### git を使って作る

```
git clone https://github.com/SeijiFukuhara/reminder.git
cd reminder
build.bat
```

### build.bat がしていること

1. 仮想環境 `.venv` がなければ作成する
2. `.venv` に customtkinter と PyInstaller（`requirements-dev.txt`）をインストールする
3. `dist\Reminder.exe` を作成する

## 新しいバージョンを公開する

`v` から始まるタグを push すると、GitHub Actions が exe を作成して Releases に公開します。

```
git tag v1.0.1
git push origin v1.0.1
```

数分後、[Releases](https://github.com/SeijiFukuhara/reminder/releases) に `Reminder.exe` が追加されます。

## 開発

### Python から直接起動する

画面には [customtkinter](https://github.com/TomSchimansky/CustomTkinter) を使っています。
仮想環境に入れてから起動してください。

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

2回目以降は `.venv\Scripts\activate` → `python main.py` だけで起動できます。

### テスト

```
python -m unittest discover -s tests -t .
```

### 構成

```
main.py                 起動スクリプト
build.bat               仮想環境の作成と exe のビルド
requirements.txt        アプリに必要なパッケージ（customtkinter）
requirements-dev.txt    ビルドに使うパッケージ（+ PyInstaller）
reminder_app/
  models.py             タスクのデータと表示ルール
  storage.py            JSONファイルへの保存・読み込み
  ui/
    app.py              メインウインドウ（タブ）
    theme.py            色・フォント
    home.py             ホーム（タスク一覧・今日のメモ）
    task_form.py        タスク登録・編集
    completed.py        完了済みタスク（日ごと）
    registered.py       登録済みタスク・メモ一覧
    widgets.py          共通部品（カレンダー、削除ボタンなど）
tests/                  テスト
.github/workflows/      exe を自動で作成・公開する設定
```
