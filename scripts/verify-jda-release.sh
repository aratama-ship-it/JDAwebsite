#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
APP_ALLOWLIST="$PROJECT_ROOT/deploy/jda-app.allowlist"
LEGACY_ALLOWLIST="$PROJECT_ROOT/deploy/jda-legacy-assets.allowlist"
DENYLIST="$PROJECT_ROOT/deploy/jda-denylist.txt"
INTEGRITY_SCRIPT="$SCRIPT_DIR/check-jda-legacy-integrity.py"

usage() {
  echo "Usage: $0 RELEASE_DIR" >&2
  exit 2
}

[ "$#" -eq 1 ] || usage
RELEASE_DIR=$1
[ -d "$RELEASE_DIR" ] || { echo "ERROR: release directory not found: $RELEASE_DIR" >&2; exit 1; }
RELEASE_DIR=$(CDPATH= cd -- "$RELEASE_DIR" && pwd -P)

manifest_entries() {
  sed -e 's/[[:space:]]*$//' -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' "$1"
}

validate_relative_path() {
  case "$1" in
    /*|../*|*/../*|*/..|.|..|'') return 1 ;;
  esac
  return 0
}

expected=$(mktemp "${TMPDIR:-/tmp}/jda-expected.XXXXXX")
actual=$(mktemp "${TMPDIR:-/tmp}/jda-actual.XXXXXX")
expected_dirs=$(mktemp "${TMPDIR:-/tmp}/jda-expected-dirs.XXXXXX")
actual_dirs=$(mktemp "${TMPDIR:-/tmp}/jda-actual-dirs.XXXXXX")
cleanup() {
  rm -f -- "$expected" "$actual" "$expected_dirs" "$actual_dirs"
}
trap cleanup EXIT HUP INT TERM

{
  manifest_entries "$APP_ALLOWLIST"
  manifest_entries "$LEGACY_ALLOWLIST"
} | LC_ALL=C sort -u > "$expected"

while IFS= read -r rel; do
  validate_relative_path "$rel" || { echo "ERROR: unsafe allowlist path: $rel" >&2; exit 1; }
done < "$expected"

(
  cd "$RELEASE_DIR"
  find . -type f -print | sed 's#^\./##' | LC_ALL=C sort
) > "$actual"

if ! diff -u "$expected" "$actual"; then
  echo "ERROR: release contents differ from the allowlist" >&2
  exit 1
fi

while IFS= read -r rel; do
  dir=$(dirname -- "$rel")
  while [ "$dir" != "." ]; do
    echo "$dir"
    dir=$(dirname -- "$dir")
  done
done < "$expected" | LC_ALL=C sort -u > "$expected_dirs"

(
  cd "$RELEASE_DIR"
  find . -mindepth 1 -type d -print | sed 's#^\./##' | LC_ALL=C sort
) > "$actual_dirs"

if ! diff -u "$expected_dirs" "$actual_dirs"; then
  echo "ERROR: release directories differ from the allowlist" >&2
  exit 1
fi

if find "$RELEASE_DIR" -type l -print | grep -q .; then
  echo "ERROR: symlinks are not allowed in the release" >&2
  find "$RELEASE_DIR" -type l -print >&2
  exit 1
fi

while IFS= read -r pattern; do
  case "$pattern" in
    ''|'#'*) continue ;;
    */)
      if [ -e "$RELEASE_DIR/${pattern%/}" ]; then
        echo "ERROR: denied directory found: $pattern" >&2
        exit 1
      fi
      ;;
    \**)
      suffix=${pattern#\*}
      if find "$RELEASE_DIR" -type f -name "*$suffix" -print | grep -q .; then
        echo "ERROR: denied extension found: $pattern" >&2
        exit 1
      fi
      ;;
    *)
      [ ! -e "$RELEASE_DIR/$pattern" ] || { echo "ERROR: denied path found: $pattern" >&2; exit 1; }
      ;;
  esac
done < "$DENYLIST"

while IFS= read -r rel; do
  case "$rel" in
    *.pdf)
      magic=$(LC_ALL=C head -c 5 "$RELEASE_DIR/$rel" || true)
      [ "$magic" = "%PDF-" ] || { echo "ERROR: not a PDF: $rel" >&2; exit 1; }
      ;;
    *.mp3)
      mime=$(file -b --mime-type "$RELEASE_DIR/$rel")
      [ "$mime" = "audio/mpeg" ] || { echo "ERROR: not an MP3: $rel ($mime)" >&2; exit 1; }
      ;;
  esac
done <<EOF
$(manifest_entries "$LEGACY_ALLOWLIST")
EOF

"$INTEGRITY_SCRIPT" "$RELEASE_DIR"

echo "OK: release matches the allowlist ($(wc -l < "$actual" | tr -d ' ') files)"
