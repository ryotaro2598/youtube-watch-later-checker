# YouTube Watch Later Checker

YouTube の「後で見る」再生リストを書き出した CSV から、再生不可の可能性がある動画を絞り込むための Python スクリプトです。

YouTube の oEmbed API で動画情報を取得できるかを確認し、全件の判定結果、再生不可候補、取得できた動画をそれぞれ CSV に出力します。

## できること

- YouTube Takeout などで取得した「後で見る」CSV を読み込む
- 動画 ID ごとに oEmbed の取得可否を確認する
- 再生不可の可能性がある動画を候補として別 CSV にまとめる
- 追加日時、動画 URL、タイトル、チャンネル名、HTTP ステータスを一覧化する

## 必要なもの

- Python 3
- インターネット接続

外部ライブラリは使っていません。標準ライブラリだけで動きます。

## 使い方

1. このリポジトリを取得します。

```bash
git clone https://github.com/YOUR_USER_NAME/youtube-watch-later-checker.git
cd youtube-watch-later-checker
```

2. YouTube の「後で見る」CSV を用意します。

CSV には、次のいずれかの動画 ID 列が必要です。

- `動画 ID`
- `video_id`
- `Video ID`
- `id`

追加日時は、次の列名がある場合に読み取られます。

- `再生リストの動画の作成タイムスタンプ`
- `added_at`
- `time`
- `created_at`

3. スクリプトを実行します。

```bash
python3 check_youtube_watch_later.py "Watch later の動画.csv"
```

## 出力ファイル

入力 CSV と同じフォルダに、次の 3 ファイルが作成されます。

| ファイル名 | 内容 |
| --- | --- |
| `watch_later_checked.csv` | 全件の判定結果 |
| `watch_later_unavailable_candidates.csv` | 再生不可の可能性がある動画、または確認エラーになった動画 |
| `watch_later_available.csv` | oEmbed で情報を取得できた動画 |

## 判定ステータス

| status | 意味 |
| --- | --- |
| `available_by_oembed` | oEmbed で動画情報を取得できた |
| `unavailable_candidate` | oEmbed で取得できず、再生不可の可能性がある |
| `check_error` | 通信失敗などで確認できなかった |

## 注意点

`unavailable_candidate` は、必ず削除済み・非公開という意味ではありません。

年齢制限、地域制限、一時的な通信エラー、YouTube 側の仕様変更などでも候補に入る可能性があります。重要な動画は、出力された `watch_url` をブラウザで開いて手動確認してください。

また、入力 CSV や出力 CSV には視聴履歴・再生リスト情報が含まれる場合があります。公開リポジトリへ誤ってアップロードしないよう注意してください。

## GitHub に公開する手順

初回だけ GitHub CLI の認証を行います。

```bash
gh auth login -h github.com
```

このフォルダで Git リポジトリを作成します。

```bash
git init
git add check_youtube_watch_later.py README.md .gitignore
git commit -m "Add YouTube watch later checker"
```

GitHub に新しいリポジトリを作って push します。

```bash
gh repo create youtube-watch-later-checker --public --source=. --remote=origin --push
```

非公開リポジトリにしたい場合は、`--public` を `--private` に変更してください。

## ライセンス

必要に応じてライセンスファイルを追加してください。
