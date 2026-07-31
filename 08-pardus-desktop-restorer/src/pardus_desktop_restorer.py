#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pardus Desktop Quick Restorer / Session Guard
XFCE (xfconf) ve GNOME (dconf) masaustu ayarlarini yedekler, panel coktugunde
tek tikla geri yukler veya varsayilana sifirlar.
Lisans: GPL-3.0
"""
import os
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QListWidget, QListWidgetItem,
                             QMessageBox, QTextEdit)

YEDEK_DIZINI = os.path.expanduser("~/.local/share/pardus-desktop-restorer")
XFCE_DIZINI = os.path.expanduser("~/.config/xfce4")
GNOME_ANAHTARLARI = ["/org/gnome/shell/", "/org/gnome/desktop/"]


def masaustu_ortami():
    ortam = (os.environ.get("XDG_CURRENT_DESKTOP") or
             os.environ.get("DESKTOP_SESSION") or "").upper()
    if "XFCE" in ortam:
        return "xfce"
    if "GNOME" in ortam:
        return "gnome"
    return "bilinmiyor"


def yedek_listesi():
    if not os.path.isdir(YEDEK_DIZINI):
        return []
    ogeler = []
    for ad in sorted(os.listdir(YEDEK_DIZINI), reverse=True):
        yol = os.path.join(YEDEK_DIZINI, ad)
        if os.path.isfile(yol) and ad.endswith(".tar.gz"):
            boyut = os.path.getsize(yol) / 1024.0
            ogeler.append((ad, yol, "%.0f KB" % boyut))
    return ogeler


def yedek_al(ortam):
    os.makedirs(YEDEK_DIZINI, exist_ok=True)
    damga = datetime.now().strftime("%Y%m%d-%H%M%S")
    hedef = os.path.join(YEDEK_DIZINI, "%s-%s.tar.gz" % (ortam, damga))
    gecici = os.path.join(YEDEK_DIZINI, ".gecici")
    if os.path.isdir(gecici):
        shutil.rmtree(gecici)
    os.makedirs(gecici)

    if ortam == "xfce" and os.path.isdir(XFCE_DIZINI):
        shutil.copytree(XFCE_DIZINI, os.path.join(gecici, "xfce4"))
    if ortam == "gnome":
        for anahtar in GNOME_ANAHTARLARI:
            ad = anahtar.strip("/").replace("/", "-") + ".dconf"
            with open(os.path.join(gecici, ad), "w") as f:
                subprocess.run(["dconf", "dump", anahtar], stdout=f)

    panel_yolu = os.path.expanduser("~/.config/xfce4/panel")
    if os.path.isdir(panel_yolu) and ortam != "xfce":
        shutil.copytree(panel_yolu, os.path.join(gecici, "panel"))

    with tarfile.open(hedef, "w:gz") as t:
        t.add(gecici, arcname="pardus-masaustu-yedegi")
    shutil.rmtree(gecici)
    return hedef


def yedek_geri_yukle(yol, ortam):
    gecici = os.path.join(YEDEK_DIZINI, ".acilan")
    if os.path.isdir(gecici):
        shutil.rmtree(gecici)
    os.makedirs(gecici)
    with tarfile.open(yol, "r:gz") as t:
        t.extractall(gecici)
    kok = os.path.join(gecici, "pardus-masaustu-yedegi")

    xfce_yedek = os.path.join(kok, "xfce4")
    if os.path.isdir(xfce_yedek):
        if os.path.isdir(XFCE_DIZINI):
            shutil.rmtree(XFCE_DIZINI)
        shutil.copytree(xfce_yedek, XFCE_DIZINI)

    for ad in os.listdir(kok):
        if ad.endswith(".dconf"):
            anahtar = "/" + ad[:-6].replace("-", "/") + "/"
            with open(os.path.join(kok, ad)) as f:
                subprocess.run(["dconf", "load", anahtar], stdin=f)

    shutil.rmtree(gecici)


def masaustu_yeniden_baslat(ortam):
    if ortam == "xfce":
        subprocess.Popen(["xfce4-panel", "-r"])
        subprocess.Popen(["xfdesktop", "--reload"])
        return "XFCE paneli ve masaustu yeniden yuklendi."
    if ortam == "gnome":
        subprocess.Popen(["killall", "-HUP", "gnome-shell"])
        return ("GNOME Shell'e yeniden yukleme sinyali gonderildi. "
                "Wayland oturumunda cikip tekrar girmeniz gerekebilir.")
    return "Masaustu ortami belirlenemedi."


def varsayilana_sifirla(ortam):
    if ortam == "xfce":
        subprocess.run(["xfconf-query", "-c", "xfce4-panel", "-p", "/", "-r", "-R"])
        panel = os.path.expanduser("~/.config/xfce4/panel")
        if os.path.isdir(panel):
            shutil.rmtree(panel)
        subprocess.Popen(["xfce4-panel", "-r"])
        return "XFCE panel ayarlari varsayilana dondu."
    if ortam == "gnome":
        for anahtar in GNOME_ANAHTARLARI:
            subprocess.run(["dconf", "reset", "-f", anahtar])
        subprocess.Popen(["killall", "-HUP", "gnome-shell"])
        return "GNOME masaustu ayarlari varsayilana dondu."
    return "Desteklenmeyen masaustu ortami."


class DesktopRestorer(QWidget):
    def __init__(self):
        super().__init__()
        self.ortam = masaustu_ortami()
        self.setWindowTitle("Pardus Masaustu Kurtarma Araci")
        self.setMinimumSize(680, 520)

        duzen = QVBoxLayout(self)
        baslik = QLabel("Masaustu Kurtarma ve Yedekleme")
        baslik.setStyleSheet("font-size:17px;font-weight:bold;")
        duzen.addWidget(baslik)
        duzen.addWidget(QLabel(
            "Algilanan masaustu ortami: %s\n"
            "Panel, simge ve tema ayarlarinizi yedekleyip bozulma durumunda "
            "tek tikla geri yukleyin." % self.ortam.upper()))

        duzen.addWidget(QLabel("Mevcut yedekler:"))
        self.liste = QListWidget()
        duzen.addWidget(self.liste)

        satir1 = QHBoxLayout()
        b1 = QPushButton("Simdi Yedek Al")
        b1.clicked.connect(self.yedekle)
        satir1.addWidget(b1)
        b2 = QPushButton("Secili Yedegi Geri Yukle")
        b2.clicked.connect(self.geri_yukle)
        satir1.addWidget(b2)
        b3 = QPushButton("Secili Yedegi Sil")
        b3.clicked.connect(self.yedek_sil)
        satir1.addWidget(b3)
        duzen.addLayout(satir1)

        satir2 = QHBoxLayout()
        b4 = QPushButton("Paneli Yeniden Baslat")
        b4.clicked.connect(self.panel_yenile)
        satir2.addWidget(b4)
        b5 = QPushButton("Masaustunu Varsayilana Sifirla")
        b5.clicked.connect(self.sifirla)
        satir2.addWidget(b5)
        duzen.addLayout(satir2)

        self.gunluk = QTextEdit()
        self.gunluk.setReadOnly(True)
        self.gunluk.setMaximumHeight(130)
        duzen.addWidget(self.gunluk)

        self.listeyi_yenile()

    def yaz(self, metin):
        self.gunluk.append(metin)

    def listeyi_yenile(self):
        self.liste.clear()
        for ad, yol, boyut in yedek_listesi():
            oge = QListWidgetItem("%s   (%s)" % (ad, boyut))
            oge.setData(Qt.UserRole, yol)
            self.liste.addItem(oge)
        if self.liste.count() == 0:
            self.yaz("Henuz yedek yok. 'Simdi Yedek Al' ile ilk yedeginizi olusturun.")

    def yedekle(self):
        try:
            yol = yedek_al(self.ortam)
        except Exception as h:
            QMessageBox.critical(self, "Hata", "Yedek alinamadi: %s" % h)
            return
        self.yaz("Yedek olusturuldu: %s" % yol)
        self.listeyi_yenile()

    def secili_yol(self):
        oge = self.liste.currentItem()
        return oge.data(Qt.UserRole) if oge else None

    def geri_yukle(self):
        yol = self.secili_yol()
        if not yol:
            QMessageBox.information(self, "Bilgi", "Once bir yedek secin.")
            return
        onay = QMessageBox.question(
            self, "Onay",
            "Mevcut masaustu ayarlariniz bu yedekle degistirilecek. Devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if onay != QMessageBox.Yes:
            return
        try:
            yedek_geri_yukle(yol, self.ortam)
        except Exception as h:
            QMessageBox.critical(self, "Hata", "Geri yukleme basarisiz: %s" % h)
            return
        self.yaz("Yedek geri yuklendi: %s" % yol)
        self.yaz(masaustu_yeniden_baslat(self.ortam))

    def yedek_sil(self):
        yol = self.secili_yol()
        if not yol:
            return
        os.remove(yol)
        self.yaz("Silindi: %s" % yol)
        self.listeyi_yenile()

    def panel_yenile(self):
        self.yaz(masaustu_yeniden_baslat(self.ortam))

    def sifirla(self):
        onay = QMessageBox.question(
            self, "Dikkat",
            "Tum panel ve masaustu ozellestirmeleriniz silinip varsayilana "
            "donecek. Once yedek almaniz onerilir.\n\nDevam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if onay != QMessageBox.Yes:
            return
        self.yaz(varsayilana_sifirla(self.ortam))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pardus Desktop Restorer")
    p = DesktopRestorer()
    p.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
