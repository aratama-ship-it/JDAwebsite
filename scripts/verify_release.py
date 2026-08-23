#!/usr/bin/env python3
"""Cyberduckへ渡すJDA本部サイト候補を、アップロードせずに検査する。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from release_config import (
    FORBIDDEN_DIRECTORY_NAMES,
    FORBIDDEN_SUFFIXES,
    LIVE_LINK_REPLACEMENTS,
    PRESERVED_LIVE_PREFIXES,
    ROOT_FILES,
)


IGNORED_SCHEMES = {"data", "http", "https", "javascript", "mailto", "tel"}
REQUIRED_FILES = (
    *ROOT_FILES,
    "css/style.css",
    "js/main.js",
    "external/about/index.html",
    "external/access/index.html",
    "external/certification/index.html",
    "external/champions/index.html",
    "external/champions/data/champions.json",
    "external/contact/index.html",
    "external/dispatch/index.html",
    "external/news/index.html",
    "external/otp2/index.html",
    "external/records/index.html",
    "external/rule/index.html",
)
HIDDEN_OR_TEMP_NAMES = {".DS_Store", "Thumbs.db"}


class ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.references.append(value)
            elif name == "srcset" and value:
                self.references.extend(
                    candidate.strip().split()[0]
                    for candidate in value.split(",")
                    if candidate.strip()
                )


def resolve_reference(public: Path, source: Path, raw_reference: str) -> Path | None:
    reference = raw_reference.strip()
    if not reference or reference.startswith("#"):
        return None

    parsed = urlsplit(reference)
    if parsed.scheme.lower() in IGNORED_SCHEMES or parsed.netloc:
        return None

    path_text = unquote(parsed.path)
    if not path_text or path_text.startswith(PRESERVED_LIVE_PREFIXES):
        return None

    if path_text.startswith("/"):
        target = public / path_text.lstrip("/")
    else:
        target = source.parent / path_text
    if path_text.endswith("/"):
        target /= "index.html"
    return target.resolve()


def add_reference_error(
    errors: list[str], public: Path, source: Path, reference: str
) -> None:
    target = resolve_reference(public, source, reference)
    if target is None:
        return
    try:
        target.relative_to(public.resolve())
    except ValueError:
        errors.append(f"公開フォルダ外への参照: {source.relative_to(public)} -> {reference}")
        return
    if not target.exists():
        errors.append(f"参照先なし: {source.relative_to(public)} -> {reference}")


def verify(candidate: Path) -> tuple[list[str], int, set[str], set[str]]:
    errors: list[str] = []
    public = candidate / "public"
    if not public.is_dir():
        return ([f"publicフォルダなし: {public}"], 0, set(), set())

    for relative in REQUIRED_FILES:
        if not (public / relative).is_file():
            errors.append(f"必須ファイルなし: {relative}")

    for path in public.rglob("*"):
        relative = path.relative_to(public)
        if path.is_symlink():
            errors.append(f"シンボリックリンクを検出: {relative}")
        if path.name in HIDDEN_OR_TEMP_NAMES or path.name.startswith("._"):
            errors.append(f"隠しファイル・一時ファイルを検出: {relative}")
        if path.name.endswith("~") or path.suffix.lower() in {".log", ".tmp"}:
            errors.append(f"一時ファイルを検出: {relative}")
        if path.is_dir() and path.name in FORBIDDEN_DIRECTORY_NAMES:
            errors.append(f"公開対象外ディレクトリを検出: {relative}")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"公開対象外ファイルを検出: {relative}")

    html_files = sorted(public.rglob("*.html"))
    readable_html: list[Path] = []
    for html_file in html_files:
        try:
            html_text = html_file.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"UTF-8で読めないHTML: {html_file.relative_to(public)} ({exc})")
            continue
        readable_html.append(html_file)
        parser = ReferenceParser()
        parser.feed(html_text)
        for reference in parser.references:
            add_reference_error(errors, public, html_file, reference)
        for reference in re.findall(r"fetch\(\s*['\"]([^'\"]+)['\"]", html_text):
            add_reference_error(errors, public, html_file, reference)

    for css_file in sorted(public.rglob("*.css")):
        css_text = css_file.read_text(encoding="utf-8")
        for reference in re.findall(r"""url\(\s*['"]?([^)'"]+)""", css_text):
            add_reference_error(errors, public, css_file, reference)

    main_js_path = public / "js/main.js"
    if main_js_path.is_file():
        main_js = main_js_path.read_text(encoding="utf-8")
        for reference in re.findall(r"fetch\(\s*['\"]([^'\"]+)['\"]", main_js):
            # 外部JS内の相対fetchは、そのJSを読み込んだHTMLのURLを基準に解決される。
            add_reference_error(errors, public, public / "index.html", reference)
    else:
        main_js = ""

    champions_file = public / "external/champions/data/champions.json"
    if champions_file.is_file():
        try:
            champions = json.loads(champions_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"champions.jsonが不正: {exc}")
        else:
            for year_group in champions:
                for item in year_group.get("items", []):
                    image_path = item.get("image")
                    if image_path and not (public / image_path).is_file():
                        errors.append(f"チャンピオン画像なし: {image_path}")

    text_paths = [*readable_html]
    if main_js_path.is_file():
        text_paths.append(main_js_path)
    all_text = "\n".join(path.read_text(encoding="utf-8") for path in text_paths)
    for local_link in LIVE_LINK_REPLACEMENTS:
        if local_link in all_text:
            errors.append(f"ローカル大会ミラーへのリンクが残っています: {local_link}")

    css_versions = set(re.findall(r"style\.css\?v=(\d+)", all_text))
    js_versions = set(re.findall(r"main\.js\?v=(\d+)", all_text))
    if len(css_versions) != 1:
        errors.append(f"CSSキャッシュ番号が不一致: {sorted(css_versions)}")
    if len(js_versions) != 1:
        errors.append(f"JSキャッシュ番号が不一致: {sorted(js_versions)}")

    file_count = sum(1 for path in public.rglob("*") if path.is_file())
    return errors, file_count, css_versions, js_versions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidate",
        type=Path,
        default=Path("release-candidate"),
        help="public/を含む生成済み候補フォルダ",
    )
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    errors, file_count, css_versions, js_versions = verify(candidate)

    if errors:
        print("FAIL: 公開候補に問題があります")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JDA本部サイト公開候補のローカル整合性に問題はありません")
    print(f"files: {file_count}")
    print(f"cache versions: css={next(iter(css_versions))} js={next(iter(js_versions))}")
    print("preserved live sites: /AJDC/ /OIDC/ /TIDC/jp/")
    print("excluded: WordPress PHP MySQL champions-poker")
    return 0


if __name__ == "__main__":
    sys.exit(main())
