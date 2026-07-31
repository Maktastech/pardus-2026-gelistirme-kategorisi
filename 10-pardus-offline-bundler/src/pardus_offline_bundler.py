#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pardus Offline Package & Dependency Bundler
Bir paketi ve tum bagimliliklarini internetli bir Pardus'ta indirip,
internetsiz makinede tek komutla kurulabilen .tar.gz paketi olusturur.
Hem grafik arayuz hem komut satiri destegi vardir.
Lisans: GPL-3.0
"""
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime

KURULUM_BETIGI = """#!/bin/bash
# Pardus Cevrimdisi Paket Kurucu
# Kullanim: sudo ./kur.sh
set -e
DIZIN="$(cd "$(dirname "$0")" && pwd)"

if [ "$EUID" -ne 0 ]; then
  echo "Bu betik yonetici yetkisi ister: sudo ./kur.sh"
  exit 1
fi

echo "== Pardus Cevrimdisi Kurulum =="
echo "Paket: __PAKET__"
echo "Olusturulma: __TARIH__"
echo

DEB_SAYISI=$(ls -1 "$DIZIN"/paketler/*.deb 2>/dev/null | wc -l)
echo "$DEB_SAYISI adet .deb kurulacak."
echo

apt-get install -y --no-download "$DIZIN"/paketler/*.deb 2>/dev/null \\
  || dpkg -i "$DIZIN"/paketler/*.deb \\
  || apt-get -f install -y --no-download

echo
echo "Kurulum tamamlandi."
"""


def komut(args, zaman_asimi=600):
    s = subprocess.run(args, capture_output=True, text=True, timeout=zaman_asimi)
    return s.returncode, (s.stdout or ""), (s.stderr or "")


def bagimlilik_listesi(paket):
    """apt-get install --print-uris ile indirilecek tum paketleri cozer."""
    kod, cikti, hata = komut(
        ["apt-get", "install", "--reinstall", "--print-uris", "-y", paket])
    if kod != 0:
        return None, hata.strip() or cikti.strip()
    urller = []
    for satir in cikti.splitlines():
        satir = satir.strip()
        if satir.startswith("'"):
            parcalar = satir.split()
            if len(parcalar) >= 2:
                urller.append((parcalar[0].strip("'"), parcalar[1]))
    return urller, None


def paketle(paket, hedef_dizin, gunluk=print):
    gunluk("Bagimliliklar cozumleniyor: %s" % paket)
    urller, hata = bagimlilik_listesi(paket)
    if urller is None:
        gunluk("HATA: %s" % hata)
        return None
    if not urller:
        gunluk("Indirilecek bir sey yok. Paket zaten guncel kurulu olabilir.")
        gunluk("Ipucu: '--reinstall' ile denenmesine ragmen bos donduyse "
               "paket adini kontrol edin.")
        return None

    gunluk("%d paket indirilecek." % len(urller))
    gecici = tempfile.mkdtemp(prefix="pardus-bundle-")
    paket_dizini = os.path.join(gecici, "paketler")
    os.makedirs(paket_dizini)

    for i, (url, dosya) in enumerate(urller, 1):
        hedef = os.path.join(paket_dizini, dosya)
        gunluk("[%d/%d] %s" % (i, len(urller), dosya))
        kod, _, hata = komut(["wget", "-q", "-O", hedef, url], 300)
        if kod != 0:
            gunluk("  indirilemedi: %s" % hata.strip())

    tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
    betik = KURULUM_BETIGI.replace("__PAKET__", paket).replace("__TARIH__", tarih)
    betik_yolu = os.path.join(gecici, "kur.sh")
    with open(betik_yolu, "w") as f:
        f.write(betik)
    os.chmod(betik_yolu, 0o755)

    with open(os.path.join(gecici, "BILGI.txt"), "w") as f:
        f.write("Pardus Cevrimdisi Paket Deposu\n")
        f.write("Ana paket : %s\n" % paket)
        f.write("Tarih     : %s\n" % tarih)
        f.write("Mimari    : %s\n" % os.uname().machine)
        f.write("Paket sayisi: %d\n\n" % len(urller))
        f.write("Kurulum: tar xzf dosya.tar.gz && cd <dizin> && sudo ./kur.sh\n\n")
        f.write("Icerik:\n")
        for _, dosya in urller:
            f.write("  - %s\n" % dosya)

    os.makedirs(hedef_dizin, exist_ok=True)
    damga = datetime.now().strftime("%Y%m%d-%H%M%S")
    cikti_yolu = os.path.join(hedef_dizin, "%s-cevrimdisi-%s.tar.gz" % (paket, damga))
    gunluk("Arsiv olusturuluyor...")
    with tarfile.open(cikti_yolu, "w:gz") as t:
        t.add(gecici, arcname="%s-cevrimdisi" % paket)
    shutil.rmtree(gecici, ignore_errors=True)
    gunluk("Tamamlandi: %s" % cikti_yolu)
    return cikti_yolu


# --------------------------- Grafik arayuz --------------------------------
def gui():
    from PyQt5.QtCore import QThread, pyqtSignal
    from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                                 QLabel, QLineEdit, QPushButton, QTextEdit,
                                 QFileDialog, QMessageBox)

    class PaketlemeIsi(QThread):
        gunluk = pyqtSignal(str)
        bitti = pyqtSignal(str)

        def __init__(self, paket, hedef):
            super().__init__()
            self.paket = paket
            self.hedef = hedef

        def run(self):
            try:
                yol = paketle(self.paket, self.hedef, self.gunluk.emit)
            except Exception as h:
                self.gunluk.emit("HATA: %s" % h)
                yol = None
            self.bitti.emit(yol or "")

    class Bundler(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Pardus Cevrimdisi Paket Hazirlayici")
            self.setMinimumSize(720, 540)
            duzen = QVBoxLayout(self)

            baslik = QLabel("Cevrimdisi Kurulum Paketi Olustur")
            baslik.setStyleSheet("font-size:17px;font-weight:bold;")
            duzen.addWidget(baslik)
            duzen.addWidget(QLabel(
                "Secilen paketi ve tum bagimliliklarini indirip, internetsiz bir "
                "Pardus makinesinde 'sudo ./kur.sh' ile kurulabilen bir arsiv uretir."))

            satir1 = QHBoxLayout()
            satir1.addWidget(QLabel("Paket adi:"))
            self.paket_kutusu = QLineEdit()
            self.paket_kutusu.setPlaceholderText("ornek: gimp, libreoffice, vlc")
            satir1.addWidget(self.paket_kutusu)
            duzen.addLayout(satir1)

            satir2 = QHBoxLayout()
            satir2.addWidget(QLabel("Kayit dizini:"))
            self.dizin_kutusu = QLineEdit(os.path.expanduser("~"))
            satir2.addWidget(self.dizin_kutusu)
            sec = QPushButton("Sec...")
            sec.clicked.connect(self.dizin_sec)
            satir2.addWidget(sec)
            duzen.addLayout(satir2)

            self.baslat_dugmesi = QPushButton("Paketi Hazirla")
            self.baslat_dugmesi.clicked.connect(self.basla)
            duzen.addWidget(self.baslat_dugmesi)

            self.gunluk = QTextEdit()
            self.gunluk.setReadOnly(True)
            self.gunluk.setStyleSheet("font-family: monospace;")
            duzen.addWidget(self.gunluk)

        def dizin_sec(self):
            d = QFileDialog.getExistingDirectory(self, "Kayit dizini",
                                                 self.dizin_kutusu.text())
            if d:
                self.dizin_kutusu.setText(d)

        def basla(self):
            paket = self.paket_kutusu.text().strip()
            if not paket:
                QMessageBox.information(self, "Bilgi", "Bir paket adi yazin.")
                return
            self.gunluk.clear()
            self.baslat_dugmesi.setEnabled(False)
            self.isci = PaketlemeIsi(paket, self.dizin_kutusu.text().strip())
            self.isci.gunluk.connect(self.gunluk.append)
            self.isci.bitti.connect(self.bitti)
            self.isci.start()

        def bitti(self, yol):
            self.baslat_dugmesi.setEnabled(True)
            if yol:
                QMessageBox.information(self, "Tamamlandi", "Arsiv olusturuldu:\n%s" % yol)
            else:
                QMessageBox.warning(self, "Basarisiz",
                                    "Paket hazirlanamadi. Gunlugu inceleyin.")

    app = QApplication(sys.argv)
    app.setApplicationName("Pardus Offline Bundler")
    p = Bundler()
    p.show()
    sys.exit(app.exec_())


def main():
    if len(sys.argv) > 1 and sys.argv[1] not in ("--gui",):
        paket = sys.argv[1]
        hedef = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
        sonuc = paketle(paket, hedef)
        sys.exit(0 if sonuc else 1)
    gui()


if __name__ == "__main__":
    main()
