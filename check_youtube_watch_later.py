#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube「後で見る」CSVから、再生不可っぽい動画候補を絞り込むスクリプト。

使い方:
  python3 check_youtube_watch_later.py "Watch later の動画.csv"

出力:
  watch_later_checked.csv              全件の判定結果
  watch_later_unavailable_candidates.csv  怪しい動画だけ
  watch_later_available.csv            oEmbedで取得できた動画だけ

注意:
  この判定は YouTube の oEmbed 取得可否を使った簡易判定です。
  「unavailable_candidate」= 必ず削除/非公開、ではありません。
  年齢制限・地域制限・一時的な通信失敗なども混ざる可能性があります。
"""

import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_SLEEP_SECONDS = 0.2
TIMEOUT_SECONDS = 15


def normalize_header(name: str) -> str:
    return (name or "").replace("\ufeff", "").strip()


def find_column(fieldnames, candidates):
    normalized = {normalize_header(f): f for f in fieldnames or []}
    for c in candidates:
        if c in normalized:
            return normalized[c]
    return None


def check_oembed(video_id: str):
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    params = urllib.parse.urlencode({"url": watch_url, "format": "json"})
    api_url = f"https://www.youtube.com/oembed?{params}"

    req = urllib.request.Request(
        api_url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; watch-later-checker/1.0)",
            "Accept": "application/json,text/plain,*/*",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as res:
            body = res.read().decode("utf-8", errors="replace")
            data = json.loads(body)
            return {
                "status": "available_by_oembed",
                "http_status": str(res.status),
                "title": data.get("title", ""),
                "author_name": data.get("author_name", ""),
                "thumbnail_url": data.get("thumbnail_url", ""),
                "error": "",
            }
    except urllib.error.HTTPError as e:
        # 401/403/404 などは「怪しい候補」として扱う
        return {
            "status": "unavailable_candidate",
            "http_status": str(e.code),
            "title": "",
            "author_name": "",
            "thumbnail_url": "",
            "error": f"HTTPError: {e.reason}",
        }
    except Exception as e:
        # 通信失敗など。後で再実行・手動確認推奨
        return {
            "status": "check_error",
            "http_status": "",
            "title": "",
            "author_name": "",
            "thumbnail_url": "",
            "error": f"{type(e).__name__}: {e}",
        }


def main():
    if len(sys.argv) < 2:
        print('使い方: python3 check_youtube_watch_later.py "Watch later の動画.csv"')
        sys.exit(1)

    input_path = Path(sys.argv[1]).expanduser()
    if not input_path.exists():
        print(f"入力ファイルが見つかりません: {input_path}")
        sys.exit(1)

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            print("CSVのヘッダーが読み取れませんでした。")
            sys.exit(1)

        video_col = find_column(reader.fieldnames, ["動画 ID", "video_id", "Video ID", "id"])
        added_col = find_column(reader.fieldnames, ["再生リストの動画の作成タイムスタンプ", "added_at", "time", "created_at"])

        if not video_col:
            print("動画IDの列が見つかりませんでした。ヘッダーを確認してください。")
            print("見つかったヘッダー:", reader.fieldnames)
            sys.exit(1)

        rows = list(reader)

    total = len(rows)
    print(f"対象動画数: {total}件")

    output_rows = []
    available_count = 0
    candidate_count = 0
    error_count = 0

    for i, row in enumerate(rows, start=1):
        video_id = (row.get(video_col) or "").strip()
        if not video_id:
            continue

        result = check_oembed(video_id)
        watch_url = f"https://www.youtube.com/watch?v={video_id}"

        out = {
            "video_id": video_id,
            "added_at": (row.get(added_col) or "").strip() if added_col else "",
            "watch_url": watch_url,
            "status": result["status"],
            "http_status": result["http_status"],
            "title": result["title"],
            "author_name": result["author_name"],
            "thumbnail_url": result["thumbnail_url"],
            "error": result["error"],
        }
        output_rows.append(out)

        if result["status"] == "available_by_oembed":
            available_count += 1
        elif result["status"] == "unavailable_candidate":
            candidate_count += 1
        else:
            error_count += 1

        if i % 25 == 0 or i == total:
            print(f"{i}/{total}件確認中... 取得OK:{available_count} 怪しい候補:{candidate_count} エラー:{error_count}")

        time.sleep(DEFAULT_SLEEP_SECONDS)

    fieldnames = [
        "video_id",
        "added_at",
        "watch_url",
        "status",
        "http_status",
        "title",
        "author_name",
        "thumbnail_url",
        "error",
    ]

    checked_path = input_path.with_name("watch_later_checked.csv")
    unavailable_path = input_path.with_name("watch_later_unavailable_candidates.csv")
    available_path = input_path.with_name("watch_later_available.csv")

    def write_csv(path, data):
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    write_csv(checked_path, output_rows)
    write_csv(unavailable_path, [r for r in output_rows if r["status"] != "available_by_oembed"])
    write_csv(available_path, [r for r in output_rows if r["status"] == "available_by_oembed"])

    print("\n完了しました。")
    print(f"全件: {checked_path}")
    print(f"怪しい候補: {unavailable_path}")
    print(f"取得OK: {available_path}")
    print("\n補足: 怪しい候補は、削除・非公開・地域制限・年齢制限・通信失敗などが混ざる可能性があります。")


if __name__ == "__main__":
    main()
