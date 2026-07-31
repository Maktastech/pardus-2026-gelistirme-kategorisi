#!/bin/bash
# Pardus App Startup & Boot Profiler - kurulum betigi
set -e

AD="pardus-boot-profiler"
KAYNAK="$(cd "$(dirname "$0")" && pwd)"

if [ "$EUID" -ne 0 ]; then
  echo "Bu betigi yonetici olarak calistirin: sudo ./install.sh"
  exit 1
fi

echo "== $AD kuruluyor =="

echo "-> Bagimliliklar kontrol ediliyor..."
apt-get update -qq || true
apt-get install -y  python3 python3-pyqt5
(apt-get install -y polkitd pkexec 2>/dev/null || apt-get install -y policykit-1 || true)

echo "-> Dosyalar kopyalaniyor..."
install -d /usr/share/$AD
install -m 755 "$KAYNAK/src/pardus_boot_profiler.py" /usr/share/$AD/pardus_boot_profiler.py

cat > /usr/bin/$AD << 'EOF'
#!/bin/bash
exec python3 /usr/share/pardus-boot-profiler/pardus_boot_profiler.py "$@"
EOF
chmod 755 /usr/bin/$AD

install -d /usr/share/applications
install -m 644 "$KAYNAK/data/$AD.desktop" /usr/share/applications/$AD.desktop

echo
echo "Kurulum tamamlandi. Baslatmak icin: $AD"
echo "Kaldirmak icin: sudo ./uninstall.sh"
