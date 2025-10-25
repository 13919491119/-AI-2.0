#!/usr/bin/env bash
set -euo pipefail

ROOT="/workspaces/-AI-2.0"
LOGDIR="$ROOT/logs/supervisor"
MAX_SIZE=$((50*1024*1024)) # 50MB
TS=$(date +%Y%m%d-%H%M%S)

mkdir -p "$LOGDIR/archive"

rotate_one() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  local size
  size=$(stat -c %s "$f" 2>/dev/null || echo 0)
  if (( size > MAX_SIZE )); then
    local base
    base=$(basename "$f")
    gzip -c "$f" > "$LOGDIR/archive/${base}.${TS}.gz" || true
    : > "$f" || true
    echo "rotated: $base -> archive/${base}.${TS}.gz" >&2
  fi
}

for f in "$LOGDIR"/*.log; do
  rotate_one "$f"
done

echo "logrotate done at $TS"
