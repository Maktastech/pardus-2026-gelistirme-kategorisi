#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pardus Dynamic RAM & OOM Crash Preventer
RAM/Swap dolulugunu izler, kilitlenme esigine gelindiginde en cok bellek
tuketen sureci tespit edip kullaniciya dondurma (SIGSTOP) veya guvenle
kapatma (SIGTERM) secenegi sunar.
Lisans: GPL-3.0
"""
import os
import signal
import sys

import psutil
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import (QIcon, QPixmap, QPainter, QColor, QBrush, QPen)
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction,
                             QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QProgressBar, QPushButton, QTableWidget,
                             QTableWidgetItem, QMessageBox, QSpinBox,
                             QHeaderView, QAbstractItemView)

UYARI_ESIGI = 85     # %
KRITIK_ESIK = 93     # %
YENILEME_MS = 2000
KORUNAN = {"systemd", "init", "dbus-daemon", "Xorg", "gnome-shell",
           "xfwm4", "xfce4-session", "gdm3", "lightdm", "logind"}


def ikon_ciz(seviye):
    """Tema bagimsiz bellek simgesi. Pardus 25 "Bilge" ikon setinde bir isim
    bulunamazsa QIcon.fromTheme bos ikon dondurur ve tepsi simgesi hic
    gorunmez; bu yuzden ikon kodla ciziliyor.
    seviye: 'normal' | 'uyari' | 'kritik'"""
    renk = {"normal": QColor("#27ae60"),
            "uyari": QColor("#e67e22"),
            "kritik": QColor("#c0392b")}[seviye]
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    # bellek modulu govdesi
    p.setPen(QPen(QColor(0, 0, 0, 90), 2))
    p.setBrush(QBrush(QColor("#34495e")))
    p.drawRoundedRect(6, 18, 52, 30, 4, 4)
    # doluluk cubuklari
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(renk))
    dolu = {"normal": 2, "uyari": 3, "kritik": 4}[seviye]
    for i in range(4):
        p.setBrush(QBrush(renk if i < dolu else QColor("#7f8c8d")))
        p.drawRect(12 + i * 11, 24, 8, 18)
    # pin ayaklari
    p.setBrush(QBrush(QColor("#95a5a6")))
    for x in (14, 26, 38, 50):
        p.drawRect(x, 48, 5, 6)
    p.end()
    return QIcon(pm)


def tepsi_ikonu_yedekli(ad, seviye="normal"):
    tema = QIcon.fromTheme(ad)
    return tema if not tema.isNull() else ikon_ciz(seviye)


def tanilama():
    app = QApplication(sys.argv)
    print("=" * 58)
    print(" Pardus RAM Guard - Tanilama")
    print("=" * 58)
    print("Sistem tepsisi mevcut mu : %s"
          % ("EVET" if QSystemTrayIcon.isSystemTrayAvailable() else "HAYIR"))
    print("Tema ikonu bulundu mu    : %s"
          % ("EVET" if not QIcon.fromTheme("utilities-system-monitor").isNull()
             else "HAYIR (kendi ikonumuz kullanilacak)"))
    print("Cizilen ikon gecerli mi  : %s"
          % ("EVET" if not ikon_ciz("normal").isNull() else "HAYIR"))
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()
    print("RAM  : %s / %s  (%%%.0f)"
          % (okunabilir(ram.used), okunabilir(ram.total), ram.percent))
    print("Swap : %s / %s" % (okunabilir(swap.used), okunabilir(swap.total)))
    print("En cok bellek tuketen 3 surec:")
    for s in en_obur_surecler(3):
        print("   %-22s %8s  (PID %d)" % (s["ad"], okunabilir(s["rss"]), s["pid"]))
    print("=" * 58)
    return 0


def okunabilir(bayt):
    for birim in ("B", "KB", "MB", "GB"):
        if bayt < 1024:
            return "%.1f %s" % (bayt, birim)
        bayt /= 1024.0
    return "%.1f TB" % bayt


def en_obur_surecler(adet=10):
    liste = []
    for p in psutil.process_iter(["pid", "name", "username", "memory_info", "status"]):
        try:
            bilgi = p.info
            rss = bilgi["memory_info"].rss if bilgi["memory_info"] else 0
            liste.append({
                "pid": bilgi["pid"],
                "ad": bilgi["name"] or "?",
                "kullanici": bilgi["username"] or "?",
                "rss": rss,
                "durum": bilgi["status"],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    liste.sort(key=lambda x: x["rss"], reverse=True)
    return liste[:adet]


class RamGuardPenceresi(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pardus RAM & OOM Koruyucu")
        self.setMinimumSize(640, 460)
        duzen = QVBoxLayout(self)

        self.baslik = QLabel("Bellek durumu izleniyor...")
        self.baslik.setStyleSheet("font-size: 15px; font-weight: bold;")
        duzen.addWidget(self.baslik)

        duzen.addWidget(QLabel("RAM"))
        self.ram_cubuk = QProgressBar()
        duzen.addWidget(self.ram_cubuk)

        duzen.addWidget(QLabel("Swap"))
        self.swap_cubuk = QProgressBar()
        duzen.addWidget(self.swap_cubuk)

        esik_satiri = QHBoxLayout()
        esik_satiri.addWidget(QLabel("Kritik esik (%):"))
        self.esik_kutusu = QSpinBox()
        self.esik_kutusu.setRange(50, 99)
        self.esik_kutusu.setValue(KRITIK_ESIK)
        esik_satiri.addWidget(self.esik_kutusu)
        esik_satiri.addStretch()
        duzen.addLayout(esik_satiri)

        duzen.addWidget(QLabel("En cok bellek tuketen surecler:"))
        self.tablo = QTableWidget(0, 5)
        self.tablo.setHorizontalHeaderLabels(
            ["PID", "Surec", "Kullanici", "Bellek", "Durum"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        duzen.addWidget(self.tablo)

        dugmeler = QHBoxLayout()
        b1 = QPushButton("Sureci Dondur (SIGSTOP)")
        b1.clicked.connect(lambda: self.sinyal_gonder(signal.SIGSTOP, "donduruldu"))
        dugmeler.addWidget(b1)
        b2 = QPushButton("Devam Ettir (SIGCONT)")
        b2.clicked.connect(lambda: self.sinyal_gonder(signal.SIGCONT, "devam ettirildi"))
        dugmeler.addWidget(b2)
        b3 = QPushButton("Guvenle Kapat (SIGTERM)")
        b3.clicked.connect(lambda: self.sinyal_gonder(signal.SIGTERM, "kapatildi"))
        dugmeler.addWidget(b3)
        duzen.addLayout(dugmeler)

    def secili_pid(self):
        satir = self.tablo.currentRow()
        if satir < 0:
            return None, None
        return (int(self.tablo.item(satir, 0).text()),
                self.tablo.item(satir, 1).text())

    def sinyal_gonder(self, sinyal, fiil):
        pid, ad = self.secili_pid()
        if pid is None:
            QMessageBox.information(self, "Bilgi", "Once bir surec secin.")
            return
        if ad in KORUNAN or pid == 1:
            QMessageBox.warning(
                self, "Engellendi",
                "'%s' kritik bir sistem sureci. Bu isleme izin verilmiyor." % ad)
            return
        onay = QMessageBox.question(
            self, "Onay", "%s (PID %d) sureci %s. Devam edilsin mi?" % (ad, pid, fiil),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if onay != QMessageBox.Yes:
            return
        try:
            os.kill(pid, sinyal)
        except PermissionError:
            QMessageBox.critical(self, "Yetki Hatasi",
                                 "Bu surec baska bir kullaniciya ait, yetkiniz yok.")
        except ProcessLookupError:
            QMessageBox.information(self, "Bilgi", "Surec zaten sonlanmis.")

    def guncelle(self, ram, swap, surecler):
        self.ram_cubuk.setValue(int(ram.percent))
        self.ram_cubuk.setFormat("%s / %s  (%%p%%)"
                                 % (okunabilir(ram.used), okunabilir(ram.total)))
        if swap.total:
            self.swap_cubuk.setValue(int(swap.percent))
            self.swap_cubuk.setFormat("%s / %s  (%%p%%)"
                                      % (okunabilir(swap.used), okunabilir(swap.total)))
        else:
            self.swap_cubuk.setValue(0)
            self.swap_cubuk.setFormat("Swap alani yok")

        esik = self.esik_kutusu.value()
        if ram.percent >= esik:
            self.baslik.setText("KRITIK: Bellek doluyor, sistem kilitlenebilir!")
            self.baslik.setStyleSheet("font-size:15px;font-weight:bold;color:#c0392b;")
        elif ram.percent >= UYARI_ESIGI:
            self.baslik.setText("Uyari: Bellek kullanimi yuksek.")
            self.baslik.setStyleSheet("font-size:15px;font-weight:bold;color:#e67e22;")
        else:
            self.baslik.setText("Bellek durumu normal.")
            self.baslik.setStyleSheet("font-size:15px;font-weight:bold;color:#27ae60;")

        self.tablo.setRowCount(len(surecler))
        for i, s in enumerate(surecler):
            for j, deger in enumerate([str(s["pid"]), s["ad"], s["kullanici"],
                                       okunabilir(s["rss"]), s["durum"]]):
                self.tablo.setItem(i, j, QTableWidgetItem(deger))


class RamGuard:
    def __init__(self, app):
        self.app = app
        self.pencere = RamGuardPenceresi()
        self.kritik_bildirildi = False

        self.tepsi = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tepsi = QSystemTrayIcon(tepsi_ikonu_yedekli("utilities-system-monitor"))
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
            self.tepsi.setToolTip("Pardus RAM Guard")
            self.tepsi.show()
        else:
            print("[ram-guard] UYARI: sistem tepsisi yok, pencere modunda "
                  "calisiliyor", flush=True)
            app.setQuitOnLastWindowClosed(True)

        if self.tepsi is None or "--tepsi" not in sys.argv:
            self.pencere_goster()

        self.zamanlayici = QTimer()
        self.zamanlayici.timeout.connect(self.tik)
        self.zamanlayici.start(YENILEME_MS)
        self.tik()

    def pencere_goster(self):
        self.pencere.show()
        self.pencere.raise_()
        self.pencere.activateWindow()

    def tepsi_tiklandi(self, sebep):
        if sebep == QSystemTrayIcon.Trigger:
            self.pencere_goster()

    def tik(self):
        ram = psutil.virtual_memory()
        swap = psutil.swap_memory()
        surecler = en_obur_surecler()
        self.pencere.guncelle(ram, swap, surecler)

        esik = self.pencere.esik_kutusu.value()
        if ram.percent >= esik:
            seviye = "kritik"
        elif ram.percent >= UYARI_ESIGI:
            seviye = "uyari"
        else:
            seviye = "normal"
        if self.tepsi is not None:
            self.tepsi.setIcon(ikon_ciz(seviye))
            self.tepsi.setToolTip("RAM: %%%.0f  |  Swap: %%%.0f"
                                  % (ram.percent, swap.percent))

        if ram.percent >= esik:
            if not self.kritik_bildirildi:
                obur = surecler[0] if surecler else None
                metin = "Bellek %%%.0f dolu." % ram.percent
                if obur:
                    metin += " En cok tuketen: %s (%s)" % (obur["ad"], okunabilir(obur["rss"]))
                if self.tepsi is not None:
                    self.tepsi.showMessage("Kilitlenme riski!", metin,
                                           QSystemTrayIcon.Critical, 8000)
                else:
                    print("[ram-guard] KRITIK: %s" % metin, flush=True)
                self.pencere_goster()
                self.kritik_bildirildi = True
        elif ram.percent < esik - 8:
            self.kritik_bildirildi = False


def main():
    if "--tani" in sys.argv:
        sys.exit(tanilama())
    app = QApplication(sys.argv)
    app.setApplicationName("Pardus RAM Guard")
    app.setWindowIcon(ikon_ciz("normal"))
    app.setQuitOnLastWindowClosed(False)
    RamGuard(app)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
