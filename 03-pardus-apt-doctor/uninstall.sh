#!/bin/bash
# Pardus Auto-Fixer & Lock Rescue Tool - kaldirma betigi
set -e
AD="pardus-apt-doctor"
if [ "$EUID" -ne 0 ]; then
  echo "Bu betigi yonetici olarak calistirin: sudo ./uninstall.sh"
  exit 1
fi
rm -f /usr/bin/$AD
rm -rf /usr/share/$AD
rm -f /usr/share/applications/$AD.desktop
rm -f /usr/share/polkit-1/actions/tr.org.pardus.aptdoctor.policy
echo "$AD kaldirildi."
