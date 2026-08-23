#!/usr/bin/env python3
"""Git管理中のソースからCyberduck用の本部サイト候補を再生成する。"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from release_config import COPY_TREES, IMAGE_FILES, LIVE_LINK_REPLACEMENTS, ROOT_FILES
from verify_release import verify


REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATED_MARKER = ".generated-jda-release"


def copy_path(source: Path, destination: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"公開候補の元ファイルがありません: {source.relative_to(REPO_ROOT)}")
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def rewrite_live_links(public: Path) -> None:
    text_files = [*public.rglob("*.html"), *public.rglob("*.js")]
    for text_file in text_files:
        original = text_file.read_text(encoding="utf-8")
        updated = original
        for local_link, live_link in LIVE_LINK_REPLACEMENTS.items():
            updated = updated.replace(local_link, live_link)
        if updated != original:
            text_file.write_text(updated, encoding="utf-8")


def git_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def git_is_dirty() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode != 0 or bool(result.stdout.strip())


def write_metadata(candidate: Path, public: Path, revision: str, dirty: bool) -> None:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    files = sorted(path for path in public.rglob("*") if path.is_file())
    source_state = "DIRTY（未コミット変更あり・本番使用不可）" if dirty else "CLEAN"

    filelist_lines = []
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        filelist_lines.append(f"{digest}  {path.relative_to(public).as_posix()}")
    (candidate / "FILELIST.sha256").write_text("\n".join(filelist_lines) + "\n", encoding="utf-8")
    (candidate / "SOURCE_COMMIT.txt").write_text(revision + "\n", encoding="utf-8")
    (candidate / "SOURCE_STATE.txt").write_text(source_state + "\n", encoding="utf-8")
    (candidate / GENERATED_MARKER).write_text(
        "このフォルダは scripts/prepare_release.py が生成しました。\n",
        encoding="utf-8",
    )
    manifest = f"""# JDA本部サイト Cyberduckアップロード候補

- 生成日時: `{generated_at}`
- 元コミット: `{revision}`
- Git作業ツリー: `{source_state}`
- 公開候補ファイル数: `{len(files)}`
- 状態: ローカル生成済み。本番未反映。

Cyberduckへ渡すのは `public/` フォルダ自体ではなく、**`public/` の中身**です。
`AJDC/`、`OIDC/`、`TIDC/`、`wp/`、`.htaccess` はアップロード・同期・削除しません。
「同期」は使わず、対象一覧を確認できる通常の「アップロード」を使います。

本番アップロード前に `docs/GITHUB_CYBERDUCK_WORKFLOW.md` の停止条件を確認し、
本人の明示承認を得てください。FTPSのパスワードはGit、ファイル、チャットに保存しません。
"""
    (candidate / "UPLOAD_MANIFEST.md").write_text(manifest, encoding="utf-8")


def safe_replace(staging: Path, output: Path) -> None:
    if output.exists():
        if not output.is_dir() or not (output / GENERATED_MARKER).is_file():
            raise RuntimeError(
                f"既存フォルダを保護するため上書きを中止しました: {output}\n"
                f"再生成できるのは {GENERATED_MARKER} を持つ候補だけです。"
            )
        shutil.rmtree(output)
    staging.replace(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "release-candidate",
        help="生成先。既定はリポジトリ内のrelease-candidate/（Git除外）",
    )
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="未コミット変更があれば生成を中止する（本番候補の最終生成用）",
    )
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output == REPO_ROOT or output == output.parent:
        print(f"FAIL: 危険な生成先です: {output}", file=sys.stderr)
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    revision = git_revision()
    dirty = git_is_dirty()
    if args.require_clean and dirty:
        print("FAIL: 未コミット変更があります。本番候補の生成を中止しました。", file=sys.stderr)
        return 1

    staging = Path(tempfile.mkdtemp(prefix=".jda-release-", dir=output.parent))
    try:
        public = staging / "public"
        public.mkdir()
        for relative in (*ROOT_FILES, *IMAGE_FILES):
            copy_path(REPO_ROOT / relative, public / relative)
        for relative in COPY_TREES:
            copy_path(REPO_ROOT / relative, public / relative)
        rewrite_live_links(public)
        write_metadata(staging, public, revision, dirty)

        errors, file_count, css_versions, js_versions = verify(staging)
        if errors:
            print("FAIL: 生成した公開候補に問題があります", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

        safe_replace(staging, output)
        print("PASS: Cyberduck用の公開候補を生成・検証しました")
        print(f"output: {output}")
        print(f"files: {file_count}")
        print(f"cache versions: css={next(iter(css_versions))} js={next(iter(js_versions))}")
        print(f"source state: {'DIRTY' if dirty else 'CLEAN'}")
        print("production upload: NOT PERFORMED")
        return 0
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        if staging.exists():
            shutil.rmtree(staging)


if __name__ == "__main__":
    sys.exit(main())
