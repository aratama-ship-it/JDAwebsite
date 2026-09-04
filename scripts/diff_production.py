#!/usr/bin/env python3
"""公開候補と、取得済みの本番の控えを突き合わせ、反映で何が変わるかを一覧にする。

本人が承認する前に「どのファイルが変わるのか」を確認するための表示。
新たな通信は行わず、backup_production.py が取得済みの控えと比較する。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {".html", ".css", ".js", ".json", ".txt"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def latest_backup(root: Path) -> Path | None:
    if not root.is_dir():
        return None
    candidates = sorted(p for p in root.iterdir() if (p / "site").is_dir())
    return candidates[-1] if candidates else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, default=REPO_ROOT / "release-candidate")
    parser.add_argument("--backups", type=Path, default=REPO_ROOT / "backups")
    parser.add_argument("--backup", type=Path, default=None, help="使う控え。既定は最新")
    args = parser.parse_args()

    public = args.candidate / "public"
    if not public.is_dir():
        print(f"FAIL: 公開候補がありません: {public}", file=sys.stderr)
        return 1

    backup = args.backup or latest_backup(args.backups)
    if backup is None:
        print("FAIL: 本番の控えがありません。先に backup_production.py を実行してください。", file=sys.stderr)
        return 1
    site = backup / "site"

    state_path = backup / "state.json"
    taken_at = json.loads(state_path.read_text(encoding="utf-8"))["takenAt"] if state_path.is_file() else "不明"

    changed: list[tuple[str, int, int]] = []
    added: list[tuple[str, int]] = []
    same: list[str] = []

    for path in sorted(p for p in public.rglob("*") if p.is_file()):
        relative = path.relative_to(public).as_posix()
        current = site / relative
        if not current.is_file():
            added.append((relative, path.stat().st_size))
        elif digest(path) != digest(current):
            changed.append((relative, current.stat().st_size, path.stat().st_size))
        else:
            same.append(relative)

    removed = sorted(
        p.relative_to(site).as_posix()
        for p in site.rglob("*")
        if p.is_file() and not (public / p.relative_to(site)).is_file()
    )

    print(f"控え: {backup.name}（取得 {taken_at}）")
    print(f"公開候補: {len(list(public.rglob('*')))} 項目中 ファイル{len(changed) + len(added) + len(same)}件")
    print()
    print(f"変更 {len(changed)}件 / 新規 {len(added)}件 / 同一 {len(same)}件 / 候補に無い(本番に残る) {len(removed)}件")

    if changed:
        print("\n## 内容が変わるファイル")
        for relative, before, after in changed:
            delta = after - before
            sign = "+" if delta >= 0 else ""
            mark = " ←ページ" if relative.endswith(".html") else ""
            print(f"  {relative}  {before:,}B → {after:,}B ({sign}{delta:,}){mark}")

    if added:
        print("\n## 新しく増えるファイル")
        for relative, size in added:
            print(f"  {relative}  {size:,}B")

    if removed:
        print("\n## 候補に含まれず、本番にそのまま残るファイル")
        print("  （このアップロードでは削除されません）")
        for relative in removed:
            print(f"  {relative}")

    if same:
        print(f"\n## 内容が同じファイル（{len(same)}件・上書きしても変化なし）")

    print()
    if not changed and not added:
        print("本番と候補は同一です。反映の必要はありません。")
    else:
        print("この内容で問題なければ、Cyberduckで公開候補を転送してください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
