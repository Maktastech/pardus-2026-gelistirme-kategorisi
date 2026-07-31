#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pardus USB Sync-Guard & Buffer Tracker  v2.0
Cekirdek yazma tamponunu (/proc/meminfo -> Dirty + Writeback) izler ve USB
bellek guvenle cikarilabilir hale gelene kadar kullaniciyi uyarir.

v2.0 degisiklikleri:
  - Tepsi simgesi tema ikonuna bagli DEGIL, QPainter ile ciziliyor. (Pardus 25
    "Bilge" ikon setinde bir isim bulunamazsa Qt bos ikon dondurur ve tepsi
    simgesi hic gorunmez; onceki surumun calismiyor gibi gorunmesinin nedeni
    buydu.)
  - Tepsi yoksa uygulama pencereyle calismaya devam eder.
  - USB tespiti yalnizca /sys/block/*/removable ile degil, sysfs yolunda "usb"
    gecip gecmedigine de bakar (VirtualBox USB gecisinde removable=0 olabilir).
  - Terminale surekli durum yazar; "yasam belirtisi" gorunur.
  - `--tani` ile tek komutta ortam raporu alinir.

Kullanim:
  pardus-usb-syncguard            # pencere + tepsi
  pardus-usb-syncguard --tepsi    # sadece tepsi (servis icin)
  pardus-usb-syncguard --tani     # tanilama raporu, arayuz acmaz
Lisans: GPL-3.0
"""
import os
import subprocess
import sys

from PyQt5.QtCore import QTimer, Qt, QT_VERSION_STR, PYQT_VERSION_STR
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction,
                             QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QProgressBar, QPushButton, QListWidget,
                             QListWidgetItem, QMessageBox)

ESIK_BYTE = 1 * 1024 * 1024
YENILEME_MS = 500
AYRINTILI = "--sessiz" not in sys.argv


def kayit(metin):
    if AYRINTILI:
        print("[sync-guard] %s" % metin, flush=True)


# --------------------------------------------------------------------- ikonlar
def ikon_ciz(durum):
    """Tema bagimsiz USB bellek simgesi. durum: 'bos' | 'yaziliyor' | 'yok'"""
    boyut = 64
    pm = QPixmap(boyut, boyut)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    govde = {"yaziliyor": QColor("#c0392b"),
             "bos": QColor("#27ae60"),
             "yok": QColor("#7f8c8d")}[durum]

    # USB bellek govdesi
    p.setPen(QPen(QColor(0, 0, 0, 90), 2))
    p.setBrush(QBrush(govde))
    p.drawRoundedRect(14, 20, 36, 34, 6, 6)
    # metal konnektor
    p.setBrush(QBrush(QColor("#bdc3c7")))
    p.drawRoundedRect(24, 6, 16, 16, 3, 3)
    # durum cizgileri (yaziliyor: iki cizgi, bos: onay isareti)
    p.setPen(QPen(QColor("#ffffff"), 5, Qt.SolidLine, Qt.RoundCap))
    if durum == "yaziliyor":
        p.drawLine(26, 30, 26, 46)
        p.drawLine(38, 30, 38, 46)
    elif durum == "bos":
        p.drawLine(22, 38, 30, 46)
        p.drawLine(30, 46, 44, 28)
    p.end()
    return QIcon(pm)


def pencere_ikonu():
    """Once temayi dene, bos donerse kendi cizdigimizi kullan."""
    tema = QIcon.fromTheme("drive-removable-media")
    if not tema.isNull():
        return tema
    return ikon_ciz("bos")


# ------------------------------------------------------------------ sistem
def meminfo():
    veri = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for satir in f:
                anahtar, _, deger = satir.partition(":")
                veri[anahtar.strip()] = int(deger.strip().split()[0]) * 1024
    except OSError:
        pass
    return veri


def kirli_bayt():
    m = meminfo()
    return m.get("Dirty", 0) + m.get("Writeback", 0)


def okunabilir(bayt):
    for birim in ("B", "KB", "MB", "GB"):
        if bayt < 1024:
            return "%.1f %s" % (bayt, birim)
        bayt /= 1024.0
    return "%.1f TB" % bayt


def _ana_aygit(temel):
    if temel.startswith(("mmcblk", "nvme")):
        return temel.split("p")[0]
    return temel.rstrip("0123456789")


def cikarilabilir_mi(ana):
    """(sonuc, gerekce) dondurur."""
    yol = "/sys/block/%s" % ana
    if not os.path.exists(yol):
        return False, "sysfs kaydi yok"
    try:
        with open(os.path.join(yol, "removable")) as f:
            if f.read().strip() == "1":
                return True, "removable=1"
    except OSError:
        pass
    # VirtualBox/bazi denetleyicilerde removable=0 olabilir; sysfs yolunda usb ara
    try:
        gercek = os.path.realpath(yol)
    except OSError:
        gercek = yol
    if "/usb" in gercek:
        return True, "sysfs yolunda usb"
    return False, "removable=0 ve usb yolu yok"


def cikarilabilir_aygitlar(hepsi=False):
    """[(aygit, ana_aygit, baglama_noktasi, gerekce)]"""
    sonuc = []
    try:
        with open("/proc/mounts", "r") as f:
            satirlar = f.readlines()
    except OSError:
        return sonuc

    for satir in satirlar:
        parcalar = satir.split()
        if len(parcalar) < 2:
            continue
        aygit, nokta = parcalar[0], parcalar[1].replace("\\040", " ")
        if not aygit.startswith(("/dev/sd", "/dev/mmcblk", "/dev/nvme")):
            continue
        temel = os.path.basename(aygit)
        ana = _ana_aygit(temel)
        uygun, gerekce = cikarilabilir_mi(ana)
        if uygun or hepsi:
            sonuc.append((aygit, "/dev/" + ana, nokta,
                           gerekce + ("" if uygun else " [ATLANDI]")))
    return sonuc


# ------------------------------------------------------------------ tanilama
def tanilama():
    print("=" * 62)
    print(" Pardus USB Sync-Guard - Tanilama Raporu")
    print("=" * 62)
    print("Python      : %s" % sys.version.split()[0])
    print("Qt / PyQt5  : %s / %s" % (QT_VERSION_STR, PYQT_VERSION_STR))
    try:
        with open("/etc/os-release") as f:
            for satir in f:
                if satir.startswith("PRETTY_NAME"):
                    print("Sistem      : %s" % satir.split("=", 1)[1].strip().strip('"'))
    except OSError:
        pass
    print("Masaustu    : %s" % (os.environ.get("XDG_CURRENT_DESKTOP") or "?"))
    print("Oturum turu : %s" % (os.environ.get("XDG_SESSION_TYPE") or "?"))
    print()

    app = QApplication(sys.argv)
    var = QSystemTrayIcon.isSystemTrayAvailable()
    print("Sistem tepsisi mevcut mu : %s" % ("EVET" if var else "HAYIR"))
    if not var:
        print("  -> XFCE panelinde 'Bildirim Alani' (Notification Area) eklentisi")
        print("     yoksa tepsi simgesi gorunmez. Panele sag tik > Panel >")
        print("     Panel Tercihleri > Ogeler > + > Bildirim Alani")
    tema = QIcon.fromTheme("drive-removable-media")
    print("Tema ikonu bulundu mu    : %s" % ("EVET" if not tema.isNull() else
                                             "HAYIR (kendi ikonumuz kullanilacak)"))
    print("Cizilen ikon gecerli mi  : %s"
          % ("EVET" if not ikon_ciz("bos").isNull() else "HAYIR"))
    print()

    print("Yazma tamponu (Dirty+Writeback): %s" % okunabilir(kirli_bayt()))
    print()
    print("Bagli blok aygitlari:")
    hepsi = cikarilabilir_aygitlar(hepsi=True)
    if not hepsi:
        print("  (hicbiri yok)")
    for aygit, ana, nokta, gerekce in hepsi:
        print("  %-14s -> %-28s  %s" % (aygit, nokta, gerekce))
    print()
    uygun = [a for a in cikarilabilir_aygitlar()]
    print("Izlenecek cikarilabilir aygit sayisi: %d" % len(uygun))
    print()
    print("udisksctl mevcut mu: %s"
          % ("EVET" if _komut_var("udisksctl") else "HAYIR (apt install udisks2)"))
    print("=" * 62)
    return 0


def _komut_var(ad):
    for dizin in os.environ.get("PATH", "/usr/bin:/bin").split(":"):
        if os.path.exists(os.path.join(dizin, ad)):
            return True
    return False


# ------------------------------------------------------------------- arayuz
class SyncGuardPenceresi(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pardus USB Sync-Guard")
        self.setWindowIcon(pencere_ikonu())
        self.setMinimumWidth(520)

        duzen = QVBoxLayout(self)

        self.durum_etiketi = QLabel("Tampon bellek izleniyor...")
        self.durum_etiketi.setWordWrap(True)
        self.durum_etiketi.setStyleSheet("font-size: 15px; font-weight: bold;")
        duzen.addWidget(self.durum_etiketi)

        self.cubuk = QProgressBar()
        self.cubuk.setRange(0, 100)
        duzen.addWidget(self.cubuk)

        self.detay_etiketi = QLabel("Diske yazilmayi bekleyen veri: 0 B")
        duzen.addWidget(self.detay_etiketi)

        duzen.addWidget(QLabel("Bagli cikarilabilir aygitlar:"))
        self.liste = QListWidget()
        duzen.addWidget(self.liste)

        self.bilgi_etiketi = QLabel("")
        self.bilgi_etiketi.setWordWrap(True)
        self.bilgi_etiketi.setStyleSheet("color:#7f8c8d;")
        duzen.addWidget(self.bilgi_etiketi)

        dugme_satiri = QHBoxLayout()
        self.sync_dugmesi = QPushButton("Simdi Diske Yaz (sync)")
        self.sync_dugmesi.clicked.connect(self.sync_calistir)
        dugme_satiri.addWidget(self.sync_dugmesi)
        self.cikar_dugmesi = QPushButton("Guvenle Cikar")
        self.cikar_dugmesi.clicked.connect(self.guvenle_cikar)
        dugme_satiri.addWidget(self.cikar_dugmesi)
        duzen.addLayout(dugme_satiri)

        self.zirve = ESIK_BYTE

    def guncelle(self, kirli, aygitlar):
        if kirli > self.zirve:
            self.zirve = kirli
        self.cubuk.setValue(int(min(100, (kirli / float(self.zirve or 1)) * 100)))
        self.cubuk.setFormat("%s bekliyor" % okunabilir(kirli))
        self.detay_etiketi.setText("Diske yazilmayi bekleyen veri: %s" % okunabilir(kirli))

        if kirli > ESIK_BYTE:
            self.durum_etiketi.setText("YAZILIYOR - USB belleginizi CIKARMAYIN!")
            self.durum_etiketi.setStyleSheet(
                "font-size:15px;font-weight:bold;color:#c0392b;")
        else:
            self.zirve = ESIK_BYTE
            self.durum_etiketi.setText("Tampon bos - aygiti guvenle cikarabilirsiniz.")
            self.durum_etiketi.setStyleSheet(
                "font-size:15px;font-weight:bold;color:#27ae60;")

        self.liste.clear()
        for aygit, ana, nokta, _ in aygitlar:
            oge = QListWidgetItem("%s  ->  %s" % (aygit, nokta))
            oge.setData(Qt.UserRole, (aygit, ana, nokta))
            self.liste.addItem(oge)
        if not aygitlar:
            self.bilgi_etiketi.setText(
                "Bagli cikarilabilir aygit yok. USB bellek takilinca burada "
                "listelenir. Takili oldugu halde gorunmuyorsa terminalde "
                "'pardus-usb-syncguard --tani' komutunu calistirin.")
        else:
            self.bilgi_etiketi.setText("")

    def sync_calistir(self):
        self.sync_dugmesi.setEnabled(False)
        kayit("sync calistiriliyor")
        subprocess.call(["sync"])
        self.sync_dugmesi.setEnabled(True)

    def guvenle_cikar(self):
        oge = self.liste.currentItem()
        if oge is None:
            QMessageBox.information(self, "Bilgi", "Once listeden bir aygit secin.")
            return
        aygit, ana, _ = oge.data(Qt.UserRole)
        if kirli_bayt() > ESIK_BYTE:
            QMessageBox.warning(self, "Bekleyin",
                                "Hala diske yazilan veri var. Tampon bosalinca "
                                "tekrar deneyin.")
            return
        subprocess.call(["sync"])
        if not _komut_var("udisksctl"):
            QMessageBox.warning(self, "Eksik arac",
                                "udisksctl bulunamadi. 'sudo apt install udisks2' "
                                "ile kurabilirsiniz.")
            return
        if subprocess.call(["udisksctl", "unmount", "-b", aygit]) != 0:
            QMessageBox.critical(self, "Hata", "Aygit ayrilamadi: %s" % aygit)
            return
        subprocess.call(["udisksctl", "power-off", "-b", ana])
        QMessageBox.information(self, "Tamam",
                                "Aygit guvenle cikarilabilir: %s" % ana)


class SyncGuard:
    def __init__(self, app, tepsi_modu):
        self.app = app
        self.pencere = SyncGuardPenceresi()
        self.onceki_yaziyordu = False
        self.tepsi = None

        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tepsi = QSystemTrayIcon(ikon_ciz("bos"))
            menu = QMenu()
            a1 = QAction("Pencereyi Goster", menu)
            a1.triggered.connect(self.pencere_goster)
            menu.addAction(a1)
            menu.addSeparator()
            a2 = QAction("Cikis", menu)
            a2.triggered.connect(app.quit)
            menu.addAction(a2)
            self.tepsi.setContextMenu(menu)
            self.tepsi.activated.connect(self.tepsi_tiklandi)
            self.tepsi.setToolTip("Pardus USB Sync-Guard")
            self.tepsi.show()
            kayit("tepsi simgesi olusturuldu")
        else:
            kayit("UYARI: sistem tepsisi yok, pencere modunda calisiliyor")
            if tepsi_modu:
                kayit("       (--tepsi verilmis olsa da pencere aciliyor)")
                tepsi_modu = False
            app.setQuitOnLastWindowClosed(True)

        if not tepsi_modu:
            self.pencere_goster()

        self.zamanlayici = QTimer()
        self.zamanlayici.timeout.connect(self.tik)
        self.zamanlayici.start(YENILEME_MS)
        self.sayac = 0
        self.tik()

    def pencere_goster(self):
        self.pencere.show()
        self.pencere.raise_()
        self.pencere.activateWindow()

    def tepsi_tiklandi(self, sebep):
        if sebep == QSystemTrayIcon.Trigger:
            if self.pencere.isVisible():
                self.pencere.hide()
            else:
                self.pencere_goster()

    def tik(self):
        kirli = kirli_bayt()
        aygitlar = cikarilabilir_aygitlar()
        self.pencere.guncelle(kirli, aygitlar)

        self.sayac += 1
        if self.sayac % 20 == 0:   # ~10 saniyede bir yasam belirtisi
            kayit("tampon=%s  aygit=%d" % (okunabilir(kirli), len(aygitlar)))

        yaziyor = kirli > ESIK_BYTE and bool(aygitlar)
        if self.tepsi is not None:
            if yaziyor:
                self.tepsi.setIcon(ikon_ciz("yaziliyor"))
                self.tepsi.setToolTip("Diske yaziliyor (%s) - USB cikarmayin!"
                                      % okunabilir(kirli))
                if not self.onceki_yaziyordu:
                    kayit("YAZMA BASLADI (%s)" % okunabilir(kirli))
                    self.tepsi.showMessage(
                        "Pardus USB Sync-Guard",
                        "Diske yazma suruyor. Belleginizi cikarmayin.",
                        QSystemTrayIcon.Warning, 4000)
            else:
                self.tepsi.setIcon(ikon_ciz("bos" if aygitlar else "yok"))
                self.tepsi.setToolTip(
                    "Tampon bos - guvenle cikarabilirsiniz." if aygitlar
                    else "Takili cikarilabilir aygit yok.")
                if self.onceki_yaziyordu and aygitlar:
                    kayit("YAZMA BITTI - guvenle cikarilabilir")
                    self.tepsi.showMessage(
                        "Pardus USB Sync-Guard",
                        "Yazma tamamlandi. Aygiti guvenle cikarabilirsiniz.",
                        QSystemTrayIcon.Information, 4000)
        self.onceki_yaziyordu = yaziyor


def main():
    if "--tani" in sys.argv:
        sys.exit(tanilama())

    kayit("baslatiliyor (Qt %s, PyQt %s)" % (QT_VERSION_STR, PYQT_VERSION_STR))
    app = QApplication(sys.argv)
    app.setApplicationName("Pardus USB Sync-Guard")
    app.setWindowIcon(pencere_ikonu())
    app.setQuitOnLastWindowClosed(False)
    SyncGuard(app, tepsi_modu="--tepsi" in sys.argv)
    kayit("calisiyor. cikmak icin Ctrl+C")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
