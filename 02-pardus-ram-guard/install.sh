#!/bin/bash
# Pardus Dynamic RAM & OOM Crash Preventer - kurulum betigi
set -e

AD="pardus-ram-guard"
KAYNAK="$(cd "$(dirname "$0")" && pwd)"

if [ "$EUID" -ne 0 ]; then
  echo "Bu betigi yonetici olarak calistirin: sudo ./install.sh"
  exit 1
fi

echo "== $AD kuruluyor =="

echo "-> Bagimliliklar kontrol ediliyor..."
apt-get update -qq || true
apt-get install -y python3 python3-psutil python3-pyqt5

echo "-> Dosyalar kopyalaniyor..."
install -d /usr/share/$AD
install -m 755 "$KAYNAK/src/pardus_ram_guard.py" /usr/share/$AD/pardus_ram_guard.py

cat > /usr/bin/$AD << 'EOF'
#!/bin/bash
exec python3 /usr/share/pardus-ram-guard/pardus_ram_guard.py "$@"
EOF
chmod 755 /usr/bin/$AD

install -d /usr/share/applications
install -m 644 "$KAYNAK/data/$AD.desktop" /usr/share/applications/$AD.desktop

echo "-> systemd kullanici servisi kuruluyor..."
install -d /usr/lib/systemd/user
install -m 644 "$KAYNAK/data/$AD.service" /usr/lib/systemd/user/$AD.service
echo
echo "Oturum acilisinda otomatik baslatmak icin (normal kullanici olarak):"
echo "  systemctl --user enable --now $AD.service"

echo
echo "Kurulum tamamlandi. Baslatmak icin: $AD"
echo "Kaldirmak icin: sudo ./uninstall.sh"
