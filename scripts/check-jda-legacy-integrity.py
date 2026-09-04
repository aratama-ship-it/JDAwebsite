#!/usr/bin/env python3
"""Verify that legacy release assets exactly match the approved SHA-256 manifest."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALLOWLIST = PROJECT_ROOT / "deploy/jda-legacy-assets.allowlist"
DEFAULT_CHECKSUMS = PROJECT_ROOT / "deploy/jda-legacy-assets.sha256"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def manifest_entries(path: Path) -> list[str]:
    entries: list[str] = []
    seen: set[str] = set()
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        value = raw.strip()
        if not value or value.startswith("#"):
            continue
        if value.startswith("/") or value in {".", ".."} or ".." in Path(value).parts:
            raise ValueError(f"{path}:{line_number}: unsafe relative path: {value}")
        if value in seen:
            raise ValueError(f"{path}:{line_number}: duplicate path: {value}")
        seen.add(value)
        entries.append(value)
    return entries


def checksum_entries(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        value = raw.strip()
        if not value or value.startswith("#"):
            continue
        parts = value.split(None, 1)
        if len(parts) != 2 or not SHA256_RE.fullmatch(parts[0]):
            raise ValueError(f"{path}:{line_number}: expected '<sha256>  <relative-path>'")
        digest, relative_path = parts[0], parts[1].strip()
        if relative_path.startswith("*"):
            relative_path = relative_path[1:]
        if relative_path.startswith("/") or relative_path in {".", ".."} or ".." in Path(relative_path).parts:
            raise ValueError(f"{path}:{line_number}: unsafe relative path: {relative_path}")
        if relative_path in entries:
            raise ValueError(f"{path}:{line_number}: duplicate path: {relative_path}")
        entries[relative_path] = digest
    return entries


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_manifest_coverage(allowlist: list[str], checksums: dict[str, str]) -> list[str]:
    errors: list[str] = []
    allowlist_set = set(allowlist)
    missing = sorted(allowlist_set - checksums.keys())
    extra = sorted(checksums.keys() - allowlist_set)
    errors.extend(f"missing approved SHA-256: {path}" for path in missing)
    errors.extend(f"checksum path is not allowlisted: {path}" for path in extra)
    return errors


def verify_root(root: Path, allowlist: list[str], checksums: dict[str, str]) -> list[str]:
    errors: list[str] = []
    resolved_root = root.resolve(strict=True)
    for relative_path in allowlist:
        candidate = root / relative_path
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(resolved_root)
        except (FileNotFoundError, ValueError):
            errors.append(f"missing or escaped legacy asset: {relative_path}")
            continue
        if not candidate.is_file() or candidate.is_symlink():
            errors.append(f"legacy asset is not a regular non-symlink file: {relative_path}")
            continue
        actual = sha256_file(candidate)
        expected = checksums[relative_path]
        if actual != expected:
            errors.append(
                f"SHA-256 mismatch: {relative_path} (expected {expected}, got {actual})"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, help="legacy asset root to verify")
    parser.add_argument("--manifest-only", action="store_true")
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument("--checksums", type=Path, default=DEFAULT_CHECKSUMS)
    args = parser.parse_args()

    if not args.manifest_only and args.root is None:
        parser.error("root is required unless --manifest-only is used")

    try:
        allowlist = manifest_entries(args.allowlist)
        checksums = checksum_entries(args.checksums)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    errors = check_manifest_coverage(allowlist, checksums)
    if not errors and not args.manifest_only:
        try:
            errors.extend(verify_root(args.root, allowlist, checksums))
        except OSError as error:
            errors.append(str(error))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.manifest_only:
        print(f"OK: SHA-256 manifest covers {len(allowlist)} legacy assets")
    else:
        print(f"OK: verified SHA-256 for {len(allowlist)} legacy assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
