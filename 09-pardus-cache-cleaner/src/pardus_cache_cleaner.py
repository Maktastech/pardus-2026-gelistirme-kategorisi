#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pardus Local Repository & Cache Cleaner
apt onbellegi, yetim paketler, eski cekirdekler, journal gunlukleri ve
kullanici cop kutusunu sistem bagimliliklarina zarar vermeden temizler.
Lisans: GPL-3.0
"""
import os
import re
import subprocess
import sys

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTreeWidget, QTreeWidgetItem,
                             QTextEdit, QMessageBox, QProgressBar)


def okunabilir(bayt):
    for birim in ("B", "KB", "MB", "GB"):
        if bayt < 1024:
            return "%.1f %s" % (bayt, birim)
        bayt /= 1024.0
    return "%.1f TB" % bayt


def dizin_boyutu(yol, uzanti=None):
    toplam = 0
    if not os.path.isdir(yol):
        return 0
    for kok, _, dosyalar in os.walk(yol):
        for d in dosyalar:
            if uzanti and not d.endswith(uzanti):
                continue
            try:
                toplam += os.path.getsize(os.path.join(kok, d))
            except OSError:
                pass
    return toplam


def komut_ciktisi(args, zaman_asimi=90):
    try:
        s = subprocess.run(args, capture_output=True, text=True, timeout=zaman_asimi)
        return s.stdout
    except Exception:
        return ""


def calisan_cekirdek():
    return os.uname().release


def eski_cekirdekler():
    """Calisan ve en son cekirdek disindaki kurulu cekirdek paketleri."""
    cikti = komut_ciktisi(["dpkg-query", "-W", "-f=${Package} ${Status}\n",
                           "linux-image-*", "linux-headers-*"])
    suan = calisan_cekirdek()
    paketler = []
    for satir in cikti.splitlines():
        parcalar = satir.split()
        if len(parcalar) < 4 or parcalar[-1] != "installed":
            continue
        paket = parcalar[0]
        if re.search(r"\d+\.\d+\.\d+", paket) is None:
            continue
        surum = re.search(r"(\d+\.\d+\.\d+[^ ]*)", paket)
        if surum and surum.group(1) in suan:
            continue
        paketler.append(paket)
    # en yeni bir tanesini koruma amacli disarida birak
    paketler.sort()
    return paketler[:-1] if len(paketler) > 1 else []


def yetim_paketler():
    cikti = komut_ciktisi(["apt-get", "-s", "autoremove"])
    paketler = []
    for satir in cikti.splitlines():
        if satir.startswith("Remv "):
            paketler.append(satir.split()[1])
    return paketler


def gorevleri_topla():
    gorevler = []

    boyut = dizin_boyutu("/var/cache/apt/archives", ".deb")
    gorevler.append({
        "anahtar": "apt_cache",
        "ad": "Indirilmis paket onbellegi (.deb)",
        "aciklama": "Kurulmus paketlerin indirilen kopyalari. Silinmesi sisteme "
                    "zarar vermez, gerekirse yeniden indirilir.",
        "kazanc": boyut,
        "ayrinti": "/var/cache/apt/archives",
    })

    yetimler = yetim_paketler()
    gorevler.append({
        "anahtar": "autoremove",
        "ad": "Artik kullanilmayan (yetim) paketler",
        "aciklama": "Bagimlilik olarak kurulmus ama artik hicbir paketin "
                    "ihtiyac duymadigi paketler.",
        "kazanc": len(yetimler) * 3 * 1024 * 1024,
        "ayrinti": ", ".join(yetimler[:25]) or "Yetim paket yok",
    })

    cekirdekler = eski_cekirdekler()
    gorevler.append({
        "anahtar": "eski_cekirdek",
        "ad": "Eski cekirdek (kernel) paketleri",
        "aciklama": "Calisan cekirdek ve bir onceki surum korunur, digerleri "
                    "kaldirilir. /boot bolumunu rahatlatir.",
        "kazanc": len(cekirdekler) * 90 * 1024 * 1024,
        "ayrinti": ", ".join(cekirdekler) or "Silinecek eski cekirdek yok",
    })

    journal_boyut = dizin_boyutu("/var/log/journal")
    gorevler.append({
        "anahtar": "journal",
        "ad": "Sistem gunlukleri (journal)",
        "aciklama": "Son 7 gun disindaki systemd gunluk kayitlari silinir.",
        "kazanc": max(0, journal_boyut - 50 * 1024 * 1024),
        "ayrinti": "/var/log/journal (toplam %s)" % okunabilir(journal_boyut),
    })

    cop = os.path.expanduser("~/.local/share/Trash")
    gorevler.append({
        "anahtar": "cop",
        "ad": "Cop kutusu",
        "aciklama": "Kullanici cop kutusundaki dosyalar kalici olarak silinir.",
        "kazanc": dizin_boyutu(cop),
        "ayrinti": cop,
    })

    onbellek = os.path.expanduser("~/.cache")
    gorevler.append({
        "anahtar": "kullanici_onbellek",
        "ad": "Kullanici onbellegi (~/.cache)",
        "aciklama": "Tarayici ve uygulama gecici dosyalari. Silinmesi "
                    "guvenlidir ama uygulamalar ilk acilista yavaslayabilir.",
        "kazanc": dizin_boyutu(onbellek),
        "ayrinti": onbellek,
    })

    return gorevler


class TemizlikIsi(QThread):
    ilerleme = pyqtSignal(str)
    bitti = pyqtSignal()

    def __init__(self, anahtarlar):
        super().__init__()
        self.anahtarlar = anahtarlar

    def _calistir(self, args):
        try:
            s = subprocess.run(args, capture_output=True, text=True, timeout=900)
            self.ilerleme.emit((s.stdout or s.stderr or "tamam").strip()[:800])
        except Exception as h:
            self.ilerleme.emit("Hata: %s" % h)

    def run(self):
        for a in self.anahtarlar:
            if a == "apt_cache":
                self.ilerleme.emit("--> apt onbellegi temizleniyor...")
                self._calistir(["pkexec", "apt-get", "clean"])
            elif a == "autoremove":
                self.ilerleme.emit("--> Yetim paketler kaldiriliyor...")
                self._calistir(["pkexec", "apt-get", "autoremove", "--purge", "-y"])
            elif a == "eski_cekirdek":
                paketler = eski_cekirdekler()
                if paketler:
                    self.ilerleme.emit("--> Eski cekirdekler kaldiriliyor: %s"
                                       % ", ".join(paketler))
                    self._calistir(["pkexec", "apt-get", "purge", "-y"] + paketler)
                else:
                    self.ilerleme.emit("--> Silinecek eski cekirdek yok.")
            elif a == "journal":
                self.ilerleme.emit("--> Eski gunlukler siliniyor...")
                self._calistir(["pkexec", "journalctl", "--vacuum-time=7d"])
            elif a == "cop":
                self.ilerleme.emit("--> Cop kutusu bosaltiliyor...")
                import shutil
                for alt in ("files", "info"):
                    yol = os.path.expanduser("~/.local/share/Trash/%s" % alt)
                    if os.path.isdir(yol):
                        shutil.rmtree(yol, ignore_errors=True)
                        os.makedirs(yol, exist_ok=True)
                self.ilerleme.emit("tamam")
            elif a == "kullanici_onbellek":
                self.ilerleme.emit("--> Kullanici onbellegi temizleniyor...")
                import shutil
                kok = os.path.expanduser("~/.cache")
                for ad in os.listdir(kok) if os.path.isdir(kok) else []:
                    yol = os.path.join(kok, ad)
                    try:
                        shutil.rmtree(yol) if os.path.isdir(yol) else os.remove(yol)
                    except OSError:
                        pass
                self.ilerleme.emit("tamam")
            self.ilerleme.emit("")
        self.bitti.emit()


class CacheCleaner(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pardus Disk Temizleyici")
        self.setMinimumSize(760, 600)

        duzen = QVBoxLayout(self)
        baslik = QLabel("Disk Alani Temizleyici")
        baslik.setStyleSheet("font-size:17px;font-weight:bold;")
        duzen.addWidget(baslik)
        self.ozet = QLabel("Taraniyor...")
        duzen.addWidget(self.ozet)

        self.agac = QTreeWidget()
        self.agac.setHeaderLabels(["Temizlenecek", "Tahmini kazanc"])
        self.agac.setColumnWidth(0, 460)
        duzen.addWidget(self.agac)

        self.gunluk = QTextEdit()
        self.gunluk.setReadOnly(True)
        self.gunluk.setMaximumHeight(150)
        self.gunluk.setStyleSheet("font-family: monospace;")
        duzen.addWidget(self.gunluk)

        alt = QHBoxLayout()
        self.tara_dugmesi = QPushButton("Yeniden Tara")
        self.tara_dugmesi.clicked.connect(self.tara)
        alt.addWidget(self.tara_dugmesi)
        self.temizle_dugmesi = QPushButton("Secilenleri Temizle")
        self.temizle_dugmesi.clicked.connect(self.temizle)
        alt.addWidget(self.temizle_dugmesi)
        duzen.addLayout(alt)

        self.tara()

    def tara(self):
        self.agac.clear()
        self.gorevler = gorevleri_topla()
        toplam = 0
        for g in self.gorevler:
            oge = QTreeWidgetItem([g["ad"], okunabilir(g["kazanc"])])
            oge.setFlags(oge.flags() | Qt.ItemIsUserCheckable)
            oge.setCheckState(0, Qt.Checked if g["anahtar"] in
                              ("apt_cache", "autoremove", "journal") else Qt.Unchecked)
            oge.setData(0, Qt.UserRole, g["anahtar"])
            alt1 = QTreeWidgetItem([g["aciklama"], ""])
            alt2 = QTreeWidgetItem([g["ayrinti"][:300], ""])
            oge.addChildren([alt1, alt2])
            self.agac.addTopLevelItem(oge)
            toplam += g["kazanc"]
        st = os.statvfs("/")
        bos = st.f_bavail * st.f_frsize
        self.ozet.setText("Kok bolumde bos alan: %s  |  Temizlikle kazanilabilecek: ~%s"
                          % (okunabilir(bos), okunabilir(toplam)))

    def temizle(self):
        secilenler = []
        for i in range(self.agac.topLevelItemCount()):
            oge = self.agac.topLevelItem(i)
            if oge.checkState(0) == Qt.Checked:
                secilenler.append(oge.data(0, Qt.UserRole))
        if not secilenler:
            QMessageBox.information(self, "Bilgi", "Temizlenecek oge secilmedi.")
            return
        onay = QMessageBox.question(
            self, "Onay", "%d islem yapilacak. Devam edilsin mi?" % len(secilenler),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if onay != QMessageBox.Yes:
            return
        self.temizle_dugmesi.setEnabled(False)
        self.tara_dugmesi.setEnabled(False)
        self.isci = TemizlikIsi(secilenler)
        self.isci.ilerleme.connect(self.gunluk.append)
        self.isci.bitti.connect(self.temizlik_bitti)
        self.isci.start()

    def temizlik_bitti(self):
        self.temizle_dugmesi.setEnabled(True)
        self.tara_dugmesi.setEnabled(True)
        self.gunluk.append("=== Temizlik tamamlandi ===")
        self.tara()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pardus Cache Cleaner")
    p = CacheCleaner()
    p.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
