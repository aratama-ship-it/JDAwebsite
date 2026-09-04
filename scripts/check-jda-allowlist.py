#!/usr/bin/env python3
"""Check that JDA runtime dependencies are covered by the deploy allowlists."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_MANIFEST = PROJECT_ROOT / "deploy/jda-app.allowlist"
LEGACY_MANIFEST = PROJECT_ROOT / "deploy/jda-legacy-assets.allowlist"


def manifest_entries(path: Path) -> list[str]:
    entries = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(entries) != len(set(entries)):
        raise ValueError(f"duplicate entries in {path.relative_to(PROJECT_ROOT)}")
    for entry in entries:
        candidate = Path(entry)
        if candidate.is_absolute() or ".." in candidate.parts or entry in {"", "."}:
            raise ValueError(f"unsafe manifest path: {entry}")
    return entries


class ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for name in ("href", "src"):
            value = values.get(name)
            if value:
                self.references.append(value)


def relative_to_root(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def main() -> int:
    try:
        app_entries = manifest_entries(APP_MANIFEST)
        legacy_entries = manifest_entries(LEGACY_MANIFEST)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    app = set(app_entries)
    legacy = set(legacy_entries)
    errors: list[str] = []
    external_assets_seen: set[str] = set()

    for rel in app_entries:
        source = PROJECT_ROOT / rel
        if not source.is_file() or source.is_symlink():
            errors.append(f"missing or symlinked app file: {rel}")

    for rel in sorted(item for item in app if item.endswith(".html")):
        page = PROJECT_ROOT / rel
        parser = ReferenceParser()
        parser.feed(page.read_text(encoding="utf-8"))
        for raw in parser.references:
            url = urlsplit(raw)
            host = (url.hostname or "").lower()
            path = unquote(url.path)

            if url.scheme or url.netloc:
                if host in {"diabolo.jp", "www.diabolo.jp"} and path.lower().endswith((".pdf", ".mp3")):
                    external_assets_seen.add(path.lstrip("/"))
                continue
            if raw.startswith(("#", "mailto:", "tel:", "data:", "javascript:")) or not path:
                continue

            target = PROJECT_ROOT / path.lstrip("/") if path.startswith("/") else page.parent / path
            if target.is_dir():
                target = target / "index.html"
            try:
                target_rel = relative_to_root(target)
            except ValueError:
                errors.append(f"reference escapes project: {rel} -> {raw}")
                continue
            if target_rel not in app:
                errors.append(f"local dependency not allowlisted: {rel} -> {target_rel}")

    css_path = PROJECT_ROOT / "css/style.css"
    for raw in re.findall(r"url\(([^)]+)\)", css_path.read_text(encoding="utf-8")):
        value = raw.strip().strip("\"'")
        url = urlsplit(value)
        if url.scheme or url.netloc or value.startswith(("data:", "#", "/")):
            continue
        target_rel = relative_to_root(css_path.parent / unquote(url.path))
        if target_rel not in app:
            errors.append(f"CSS dependency not allowlisted: css/style.css -> {target_rel}")

    champions_path = PROJECT_ROOT / "champions/data/champions.json"
    champions = json.loads(champions_path.read_text(encoding="utf-8"))
    for group in champions:
        for item in group.get("items", []):
            image = item.get("image")
            if image and image not in app:
                errors.append(f"champions image not allowlisted: {image}")

    for required in ("marquee-updates.txt", "images/poker/cardback.webp"):
        if required not in app:
            errors.append(f"dynamic dependency not allowlisted: {required}")

    missing_legacy = sorted(external_assets_seen - legacy)
    unused_legacy = sorted(legacy - external_assets_seen)
    for rel in missing_legacy:
        errors.append(f"same-domain PDF/MP3 not in legacy allowlist: {rel}")
    for rel in unused_legacy:
        errors.append(f"legacy allowlist entry is no longer referenced: {rel}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        "OK: allowlists cover runtime dependencies "
        f"({len(app)} app files, {len(legacy)} legacy assets)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
