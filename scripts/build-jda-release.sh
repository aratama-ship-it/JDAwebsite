#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
APP_ALLOWLIST="$PROJECT_ROOT/deploy/jda-app.allowlist"
LEGACY_ALLOWLIST="$PROJECT_ROOT/deploy/jda-legacy-assets.allowlist"
VERIFY_SCRIPT="$SCRIPT_DIR/verify-jda-release.sh"
CHECK_SCRIPT="$SCRIPT_DIR/check-jda-allowlist.py"
INTEGRITY_SCRIPT="$SCRIPT_DIR/check-jda-legacy-integrity.py"

usage() {
  cat >&2 <<'EOF'
Usage:
  scripts/build-jda-release.sh --check
  scripts/build-jda-release.sh OUTPUT_DIR APPROVED_LEGACY_DOCROOT

OUTPUT_DIR must not already exist. APPROVED_LEGACY_DOCROOT must be an inspected
snapshot of the current site; the script copies only files listed in
deploy/jda-legacy-assets.allowlist.
EOF
  exit 2
}

manifest_entries() {
  sed -e 's/[[:space:]]*$//' -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' "$1"
}

validate_relative_path() {
  case "$1" in
    /*|../*|*/../*|*/..|.|..|'') return 1 ;;
  esac
  return 0
}

no_symlink_components() (
  source_root=$1
  rel=$2
  current=$source_root
  old_ifs=$IFS
  IFS='/'; set -- $rel; IFS=$old_ifs
  for component do
    current="$current/$component"
    [ ! -L "$current" ] || return 1
  done
  return 0
)

check_manifest_source() {
  source_root=$1
  manifest=$2
  label=$3
  missing=0

  while IFS= read -r rel; do
    validate_relative_path "$rel" || { echo "ERROR: unsafe $label path: $rel" >&2; exit 1; }
    if [ ! -f "$source_root/$rel" ] || ! no_symlink_components "$source_root" "$rel"; then
      echo "ERROR: missing or symlinked $label file: $rel" >&2
      missing=1
    fi
  done <<EOF
$(manifest_entries "$manifest")
EOF

  [ "$missing" -eq 0 ]
}

if [ "$#" -eq 1 ] && [ "$1" = "--check" ]; then
  check_manifest_source "$PROJECT_ROOT" "$APP_ALLOWLIST" "app"
  "$CHECK_SCRIPT"
  "$INTEGRITY_SCRIPT" --manifest-only
  exit 0
fi

[ "$#" -eq 2 ] || usage
OUTPUT_DIR=$1
LEGACY_ROOT=$2

[ -d "$LEGACY_ROOT" ] || { echo "ERROR: approved legacy docroot not found: $LEGACY_ROOT" >&2; exit 1; }
LEGACY_ROOT=$(CDPATH= cd -- "$LEGACY_ROOT" && pwd -P)
[ ! -e "$OUTPUT_DIR" ] || { echo "ERROR: output already exists; refusing to overwrite: $OUTPUT_DIR" >&2; exit 1; }

check_manifest_source "$PROJECT_ROOT" "$APP_ALLOWLIST" "app"
check_manifest_source "$LEGACY_ROOT" "$LEGACY_ALLOWLIST" "legacy"
"$CHECK_SCRIPT"
"$INTEGRITY_SCRIPT" "$LEGACY_ROOT"

output_parent=$(dirname -- "$OUTPUT_DIR")
mkdir -p -- "$output_parent"
output_parent=$(CDPATH= cd -- "$output_parent" && pwd)
output_name=$(basename -- "$OUTPUT_DIR")
stage=$(mktemp -d "$output_parent/.${output_name}.tmp.XXXXXX")
cleanup() {
  if [ -n "${stage:-}" ] && [ -d "$stage" ]; then
    rm -rf -- "$stage"
  fi
}
trap cleanup EXIT HUP INT TERM

copy_manifest() {
  source_root=$1
  manifest=$2
  while IFS= read -r rel; do
    mkdir -p -- "$stage/$(dirname -- "$rel")"
    cp -p -- "$source_root/$rel" "$stage/$rel"
  done <<EOF
$(manifest_entries "$manifest")
EOF
}

copy_manifest "$PROJECT_ROOT" "$APP_ALLOWLIST"
copy_manifest "$LEGACY_ROOT" "$LEGACY_ALLOWLIST"

"$VERIFY_SCRIPT" "$stage"
mv -- "$stage" "$output_parent/$output_name"
stage=''
trap - EXIT HUP INT TERM

echo "Built: $output_parent/$output_name"
