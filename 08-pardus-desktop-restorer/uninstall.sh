#!/bin/bash
# Pardus Desktop Quick Restorer / Session Guard - kaldirma betigi
set -e
AD="pardus-desktop-restorer"
if [ "$EUID" -ne 0 ]; then
  echo "Bu betigi yonetici olarak calistirin: sudo ./uninstall.sh"
  exit 1
fi

rm -f /usr/bin/$AD
rm -rf /usr/share/$AD
rm -f /usr/share/applications/$AD.desktop
echo "$AD kaldirildi."
