#!/bin/bash
# Pardus Dynamic RAM & OOM Crash Preventer - kaldirma betigi
set -e
AD="pardus-ram-guard"
if [ "$EUID" -ne 0 ]; then
  echo "Bu betigi yonetici olarak calistirin: sudo ./uninstall.sh"
  exit 1
fi

systemctl --user disable --now $AD.service 2>/dev/null || true
rm -f /usr/lib/systemd/user/$AD.service

rm -f /usr/bin/$AD
rm -rf /usr/share/$AD
rm -f /usr/share/applications/$AD.desktop
echo "$AD kaldirildi."
