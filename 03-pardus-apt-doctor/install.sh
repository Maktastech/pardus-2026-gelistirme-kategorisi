#!/bin/bash
# Pardus Auto-Fixer & Lock Rescue Tool - kurulum betigi
set -e

AD="pardus-apt-doctor"
KAYNAK="$(cd "$(dirname "$0")" && pwd)"

if [ "$EUID" -ne 0 ]; then
  echo "Bu betigi yonetici olarak calistirin: sudo ./install.sh"
  exit 1
fi

echo "== $AD kuruluyor =="

echo "-> Bagimliliklar kontrol ediliyor..."
apt-get update -qq || true
# Debian 12/Pardus 25'te policykit-1 kaldirildi; yerine polkitd + pkexec geldi.
apt-get install -y python3 python3-pyqt5
if ! apt-get install -y polkitd pkexec 2>/dev/null; then
  echo "   polkitd/pkexec bulunamadi, eski paket adi deneniyor..."
  apt-get install -y policykit-1 || true
fi

if ! command -v pkexec >/dev/null 2>&1; then
  echo "UYARI: pkexec bulunamadi. Onarim islemleri calismayacaktir."
fi

echo "-> Dosyalar kopyalaniyor..."
install -d /usr/share/$AD
install -m 755 "$KAYNAK/src/pardus_apt_doctor.py" /usr/share/$AD/pardus_apt_doctor.py
# Yonetici yardimcisi: pkexec guvenlik geregi root'a ait ve baskalarina
# yazilamaz olmalidir.
install -o root -g root -m 755 "$KAYNAK/src/apt_doctor_helper.py" \
  /usr/share/$AD/pardus-apt-doctor-helper

cat > /usr/bin/$AD << 'EOF'
#!/bin/bash
exec python3 /usr/share/pardus-apt-doctor/pardus_apt_doctor.py "$@"
EOF
chmod 755 /usr/bin/$AD

echo "-> Polkit kurali kuruluyor (tek seferlik ve Turkce sifre penceresi)..."
install -d /usr/share/polkit-1/actions
install -m 644 "$KAYNAK/data/tr.org.pardus.aptdoctor.policy" \
  /usr/share/polkit-1/actions/tr.org.pardus.aptdoctor.policy

install -d /usr/share/applications
install -m 644 "$KAYNAK/data/$AD.desktop" /usr/share/applications/$AD.desktop

echo
echo "Kurulum tamamlandi. Baslatmak icin: $AD"
echo "Kaldirmak icin: sudo ./uninstall.sh"
