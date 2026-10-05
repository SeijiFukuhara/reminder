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

Python 3.10 以上が入った Windows PC で、次を実行します。

```
git clone https://github.com/SeijiFukuhara/reminder.git
cd reminder
build.bat
```

`build.bat` は次のことを自動で行います。

1. 仮想環境 `.venv` がなければ作成する
2. `.venv` に PyInstaller（`requirements-dev.txt`）をインストールする
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

```
python main.py
```

アプリ本体は標準ライブラリ（tkinter）だけで動くので、追加のインストールは不要です。

### テスト

```
python -m unittest discover -s tests -t .
```

### 構成

```
main.py                 起動スクリプト
build.bat               仮想環境の作成と exe のビルド
requirements-dev.txt    ビルドに使うパッケージ（PyInstaller）
reminder_app/
  models.py             タスクのデータと表示ルール
  storage.py            JSONファイルへの保存・読み込み
  ui/
    app.py              メインウインドウ（タブ）
    home.py             ホーム（タスク一覧・今日のメモ）
    task_form.py        タスク登録・編集
    completed.py        完了済みタスク（日ごと）
    registered.py       登録済みタスク・メモ一覧
    widgets.py          共通部品
tests/                  テスト
.github/workflows/      exe を自動で作成・公開する設定
```
