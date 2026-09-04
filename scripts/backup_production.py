#!/usr/bin/env python3
"""本番へ上書きする前に、上書き対象と同じ範囲の現行ファイルを取得して控えを作る。

ロリポップのバックアップオプションが未契約のため、ロールバック手段を自前で用意する。
公開候補に含まれるパスだけを https://www.diabolo.jp から取得するので、
AJDC/ OIDC/ TIDC/ wp/ などの触らない領域には一切アクセスしない。
FTPの認証情報は使わない（公開URLからの取得のみ）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ORIGIN = "https://www.diabolo.jp"
USER_AGENT = "JDA-backup-script/1.0 (pre-upload rollback snapshot)"
REQUEST_INTERVAL = 0.2


def fetch(url: str, timeout: int = 30) -> tuple[int, bytes | None]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, None
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"  取得失敗: {url} ({error})", file=sys.stderr)
        return 0, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidate",
        type=Path,
        default=REPO_ROOT / "release-candidate",
        help="public/ を含む公開候補。ここに入っているパスだけを控える",
    )
    parser.add_argument("--origin", default=DEFAULT_ORIGIN, help="取得元のオリジン")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "backups",
        help="控えの保存先。日時ごとのフォルダを作る",
    )
    args = parser.parse_args()

    public = args.candidate / "public"
    if not public.is_dir():
        print(f"FAIL: 公開候補がありません: {public}", file=sys.stderr)
        print("先に ./scripts/prepare_release.sh を実行してください。", file=sys.stderr)
        return 1

    relatives = sorted(
        path.relative_to(public).as_posix()
        for path in public.rglob("*")
        if path.is_file()
    )
    if not relatives:
        print("FAIL: 公開候補が空です", file=sys.stderr)
        return 1

    stamp = datetime.now().astimezone()
    destination = args.output / stamp.strftime("%Y-%m-%d_%H%M%S")
    site = destination / "site"
    site.mkdir(parents=True, exist_ok=False)

    print(f"取得元: {args.origin}")
    print(f"対象: {len(relatives)}ファイル（公開候補と同じ範囲）")

    saved: list[tuple[str, str, int]] = []
    absent: list[str] = []
    failed: list[tuple[str, int]] = []

    for index, relative in enumerate(relatives, 1):
        status, body = fetch(f"{args.origin}/{relative}")
        if status == 200 and body is not None:
            target = site / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
            saved.append((relative, hashlib.sha256(body).hexdigest(), len(body)))
        elif status == 404:
            absent.append(relative)
        else:
            failed.append((relative, status))
        if index % 10 == 0 or index == len(relatives):
            print(f"  {index}/{len(relatives)}")
        time.sleep(REQUEST_INTERVAL)

    (destination / "FILELIST.sha256").write_text(
        "\n".join(f"{digest}  {relative}" for relative, digest, _ in saved) + "\n",
        encoding="utf-8",
    )
    (destination / "state.json").write_text(
        json.dumps(
            {
                "takenAt": stamp.isoformat(timespec="seconds"),
                "origin": args.origin,
                "candidateFiles": len(relatives),
                "savedFiles": len(saved),
                "absentOnProduction": absent,
                "failed": [{"path": p, "status": s} for p, s in failed],
                "totalBytes": sum(size for _, _, size in saved),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    absent_block = (
        "\n".join(f"- `{path}`" for path in absent)
        if absent
        else "- なし（公開候補のすべてが本番に存在する）"
    )
    (destination / "ROLLBACK.md").write_text(
        f"""# 本番のロールバック手順

取得日時: `{stamp.isoformat(timespec="seconds")}`
取得元: `{args.origin}`
控えたファイル: `{len(saved)}` 件（`site/` 配下）

この控えは、公開候補と**同じ範囲**の本番ファイルを公開URLから取得したものです。
`AJDC/`、`OIDC/`、`TIDC/`、`wp/`、`.htaccess` には触れていません。

## 戻し方

1. Cyberduckで `diabolo.jp` へ接続する（FTP-SSL Explicit AUTH TLS）。
2. `site/` の**中身**を、公開ルートへ通常の「アップロード」で転送する。「同期」は使わない。
3. 下の「本番に存在しなかったファイル」は、今回の反映で**新規に増えたもの**なので、
   完全に戻すならサーバー上から削除する。

## 本番に存在しなかったファイル（戻す際は削除する対象）

{absent_block}

## 注意

- この控えは公開URLから取得したものです。サーバー上の実ファイルと内容は一致しますが、
  パーミッションやタイムスタンプは再現されません。
- 取得できなかったファイルがある場合は `state.json` の `failed` を確認してください。
""",
        encoding="utf-8",
    )

    print()
    print("PASS: 本番の控えを取得しました" if not failed else "WARN: 一部を取得できませんでした")
    print(f"output: {destination}")
    print(f"saved: {len(saved)} / absent(本番に無い=新規追加分): {len(absent)} / failed: {len(failed)}")
    print(f"size: {sum(size for _, _, size in saved) / 1024 / 1024:.1f} MB")
    if failed:
        for path, status in failed:
            print(f"  失敗 {status}: {path}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
