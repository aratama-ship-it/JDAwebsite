#!/usr/bin/env python3
"""転送の直前に、公開候補が生成時のままかを確認する。

公開候補は生成後も汚れる。Finderでフォルダを開くだけで .DS_Store が作られるため、
「生成時に検証済み」では転送時の安全を保証できない。
OSが作る不要ファイルを取り除いてから、生成時と同じ検査を実行する。
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_release import HIDDEN_OR_TEMP_NAMES, verify  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def remove_os_junk(public: Path) -> list[str]:
    removed = []
    for path in sorted(public.rglob("*")):
        if path.is_file() and (path.name in HIDDEN_OR_TEMP_NAMES or path.name.startswith("._")):
            removed.append(path.relative_to(public).as_posix())
            path.unlink()
    return removed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, default=REPO_ROOT / "release-candidate")
    args = parser.parse_args()

    candidate = args.candidate
    public = candidate / "public"
    if not public.is_dir():
        print(f"FAIL: 公開候補がありません: {public}", file=sys.stderr)
        return 1

    removed = remove_os_junk(public)
    if removed:
        print(f"OSが作った不要ファイルを {len(removed)} 件取り除きました:")
        for relative in removed:
            print(f"  - {relative}")
        print()

    errors, file_count, css_versions, js_versions = verify(candidate)
    if errors:
        print("FAIL: 転送してはいけません。公開候補に問題があります", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    # 生成時のFILELISTと突き合わせ、候補が作られた後で中身が変わっていないか見る
    filelist = candidate / "FILELIST.sha256"
    drift: list[str] = []
    if filelist.is_file():
        recorded = {}
        for line in filelist.read_text(encoding="utf-8").splitlines():
            if "  " in line:
                digest, relative = line.split("  ", 1)
                recorded[relative] = digest
        for path in sorted(p for p in public.rglob("*") if p.is_file()):
            relative = path.relative_to(public).as_posix()
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if relative not in recorded:
                drift.append(f"生成後に増えた: {relative}")
            elif recorded[relative] != actual:
                drift.append(f"生成後に変わった: {relative}")
        for relative in recorded:
            if not (public / relative).is_file():
                drift.append(f"生成後に消えた: {relative}")

    if drift:
        print("FAIL: 生成時と中身が違います。作り直してください", file=sys.stderr)
        for item in drift:
            print(f"- {item}", file=sys.stderr)
        return 1

    state = (candidate / "SOURCE_STATE.txt").read_text(encoding="utf-8").strip()
    print("PASS: 転送してよい状態です")
    print(f"files: {file_count}")
    print(f"cache versions: css={next(iter(css_versions))} js={next(iter(js_versions))}")
    print(f"source state: {state}")
    if state != "CLEAN":
        print("WARN: 本番に使う候補は SOURCE_STATE が CLEAN のものにしてください", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
