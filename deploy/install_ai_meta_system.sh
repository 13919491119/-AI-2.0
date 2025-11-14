#!/usr/bin/env bash
# Install helper for systemd unit: copies unit to /etc/systemd/system and enables it.
set -euo pipefail

UNIT_SRC="$(pwd)/deploy/ai_meta_system.service"
UNIT_DST="/etc/systemd/system/ai_meta_system.service"

if [ "$(id -u)" -ne 0 ]; then
  echo "This installer requires sudo/root. Run: sudo $0" >&2
  exit 2
fi

if [ ! -f "$UNIT_SRC" ]; then
  echo "Unit file not found: $UNIT_SRC" >&2
  exit 1
fi

cp "$UNIT_SRC" "$UNIT_DST"
chmod 644 "$UNIT_DST"
systemctl daemon-reload
systemctl enable --now ai_meta_system.service
echo "Installed and started ai_meta_system.service"

echo "Check logs with: sudo journalctl -u ai_meta_system.service -f"
