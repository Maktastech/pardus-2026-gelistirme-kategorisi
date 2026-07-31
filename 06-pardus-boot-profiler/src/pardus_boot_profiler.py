#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pardus App Startup & Boot Profiler
systemd-analyze verilerini grafiklestirir, acilisi geciktiren servisleri
listeler ve gereksiz olanlari tek tikla devre disi birakir.
Lisans: GPL-3.0
"""
import os
import re
import subprocess
import sys
import logging

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QMessageBox,
                             QProgressBar, QTextEdit)

from ayristirma import KORUNAN, GEREKSIZ_OLABILIR, sureyi_saniyeye_cevir, acilis_ozeti, blame_listesi, birim_durumu


class YuklemeIsi(QThread):
    sonuc = pyqtSignal(list, str)

    def run(self):
        liste = blame_listesi()
        for s in liste[:40]:
            s["durum"] = birim_durumu(s["birim"])
        for s in liste[40:]:
            s["durum"] = "-"
        self.sonuc.emit(liste, acilis_ozeti())


class BootProfiler(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pardus Acilis Analiz Paneli")
        self.setMinimumSize(900, 620)
        self.veri = []

        duzen = QVBoxLayout(self)
        baslik = QLabel("Acilis Suresi Analizi")
        baslik.setStyleSheet("font-size:17px;font-weight:bold;")
        duzen.addWidget(baslik)

        self.ozet = QLabel("Olculuyor...")
        self.ozet.setWordWrap(True)
        duzen.addWidget(self.ozet)

        self.tablo = QTableWidget(0, 5)
        self.tablo.setHorizontalHeaderLabels(
            ["Birim", "Sure", "Pay", "Acilista", "Oneri"])
        self.tablo.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        duzen.addWidget(self.tablo)

        alt = QHBoxLayout()
        b1 = QPushButton("Yenile")
        b1.clicked.connect(self.yukle)
        alt.addWidget(b1)
        b2 = QPushButton("Secili Servisi Devre Disi Birak")
        b2.clicked.connect(lambda: self.servis_degistir("disable"))
        alt.addWidget(b2)
        b3 = QPushButton("Yeniden Etkinlestir")
        b3.clicked.connect(lambda: self.servis_degistir("enable"))
        alt.addWidget(b3)
        b4 = QPushButton("Yedek Listesi Kaydet")
        b4.clicked.connect(self.yedek_kaydet)
        alt.addWidget(b4)
        duzen.addLayout(alt)

        self.gunluk = QTextEdit()
        self.gunluk.setReadOnly(True)
        self.gunluk.setMaximumHeight(110)
        self.gunluk.setStyleSheet("font-family: monospace;")
        duzen.addWidget(self.gunluk)

        self.yukle()

    def yukle(self):
        self.ozet.setText("systemd verileri okunuyor...")
        self.isci = YuklemeIsi()
        self.isci.sonuc.connect(self.doldur)
        self.isci.start()

    def doldur(self, veri, ozet):
        self.veri = veri
        self.ozet.setText(ozet)
        toplam = sum(s["saniye"] for s in veri) or 1.0
        self.tablo.setRowCount(len(veri))
        for i, s in enumerate(veri):
            pay = 100.0 * s["saniye"] / toplam
            oneri = GEREKSIZ_OLABILIR.get(s["birim"], "")
            if s["birim"] in KORUNAN:
                oneri = "Sistem icin gerekli - kapatmayin"
            hucreler = [s["birim"], s["sure_metni"], "%%%.1f" % pay,
                        s.get("durum", "-"), oneri]
            for j, deger in enumerate(hucreler):
                oge = QTableWidgetItem(deger)
                if s["birim"] in KORUNAN:
                    oge.setBackground(QColor("#e8e8e8"))
                elif s["birim"] in GEREKSIZ_OLABILIR:
                    oge.setBackground(QColor("#fff3cd"))
                elif s["saniye"] > 5:
                    oge.setBackground(QColor("#f8d7da"))
                self.tablo.setItem(i, j, oge)

    def secili_birim(self):
        satir = self.tablo.currentRow()
        if satir < 0 or satir >= len(self.veri):
            return None
        return self.veri[satir]["birim"]

    def servis_degistir(self, eylem):
        birim = self.secili_birim()
        if birim is None:
            QMessageBox.information(self, "Bilgi", "Once bir servis secin.")
            return
        if not birim.endswith(".service"):
            QMessageBox.information(
                self, "Bilgi",
                "Yalnizca .service birimleri bu panelden degistirilebilir.")
            return
        if eylem == "disable" and birim in KORUNAN:
            QMessageBox.warning(self, "Engellendi",
                                "'%s' sistemin calismasi icin gerekli. "
                                "Bu servis kapatilamaz." % birim)
            return
        onay = QMessageBox.question(
            self, "Onay",
            "%s servisi '%s' yapilacak. Devam edilsin mi?\n\n"
            "Not: Degisiklik bir sonraki acilista etkili olur." % (birim, eylem),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if onay != QMessageBox.Yes:
            return
        s = subprocess.run(["pkexec", "systemctl", eylem, birim],
                           capture_output=True, text=True)
        self.gunluk.append("%s %s -> %s" % (eylem, birim,
                                            s.stdout.strip() or s.stderr.strip() or "tamam"))
        self.yukle()

    def yedek_kaydet(self):
        yol = os.path.expanduser("~/pardus-acilis-yedegi.txt")
        s = subprocess.run(["systemctl", "list-unit-files", "--state=enabled",
                            "--no-pager", "--no-legend"],
                           capture_output=True, text=True)
        with open(yol, "w") as f:
            f.write(s.stdout)
        QMessageBox.information(
            self, "Kaydedildi",
            "Etkin servis listesi kaydedildi:\n%s\n\n"
            "Bir sorun cikarsa bu listeye bakip servisleri geri acabilirsiniz." % yol)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pardus Boot Profiler")
    p = BootProfiler()
    p.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
