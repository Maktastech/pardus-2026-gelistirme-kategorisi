#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pardus Auto-Fixer & Lock Rescue Tool
apt/dpkg kilitlerini, yarim kalmis kurulumlari ve kirik bagimliliklari tespit
edip onarir.

Yetki modeli: acilista BIR KEZ pkexec ile bir yonetici yardimcisi baslatilir,
sonraki tum islemler bu surec uzerinden yapilir; tekrar sifre sorulmaz.
Lisans: GPL-3.0
"""
import json
import os
import subprocess
import sys
import logging

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTextEdit, QTreeWidget,
                             QTreeWidgetItem, QMessageBox)

YARDIMCI_YOLLARI = [
    "/usr/share/pardus-apt-doctor/pardus-apt-doctor-helper",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "apt_doctor_helper.py"),
]


def yardimci_yolu():
    for yol in YARDIMCI_YOLLARI:
        if os.path.exists(yol):
            return yol
    return None


class YardimciOkuyucu(QThread):
    """Yardimci surecin stdout'unu satir satir okur."""
    mesaj = pyqtSignal(dict)
    kapandi = pyqtSignal()

    def __init__(self, surec):
        super().__init__()
        self.surec = surec

    def run(self):
        try:
            for satir in self.surec.stdout:
                satir = satir.strip()
                if not satir:
                    continue
                try:
                    self.mesaj.emit(json.loads(satir))
                except ValueError:
                    self.mesaj.emit({"tur": "gunluk", "metin": satir})
        except (OSError, BrokenPipeError) as e:
            logging.error("AptDoctor Okuyucu hatasi: %s", e)
        self.kapandi.emit()


class AptDoctor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pardus Paket Sistemi Onarim Araci")
        self.setMinimumSize(760, 620)
        self.surec = None
        self.okuyucu = None
        self.sorunlar = []

        duzen = QVBoxLayout(self)
        baslik = QLabel("Paket Sistemi Saglik Kontrolu")
        baslik.setStyleSheet("font-size:17px;font-weight:bold;")
        duzen.addWidget(baslik)
        self.durum = QLabel("Yonetici yetkisi bekleniyor...")
        self.durum.setWordWrap(True)
        duzen.addWidget(self.durum)

        self.agac = QTreeWidget()
        self.agac.setHeaderLabels(["Bulgu", "Tur"])
        self.agac.setColumnWidth(0, 560)
        duzen.addWidget(self.agac)

        self.gunluk = QTextEdit()
        self.gunluk.setReadOnly(True)
        self.gunluk.setMaximumHeight(170)
        self.gunluk.setStyleSheet("font-family: monospace;")
        duzen.addWidget(self.gunluk)

        satir = QHBoxLayout()
        self.tara_dugmesi = QPushButton("Yeniden Tara")
        self.tara_dugmesi.clicked.connect(self.tara)
        satir.addWidget(self.tara_dugmesi)
        self.onar_dugmesi = QPushButton("Secili Sorunlari Onar")
        self.onar_dugmesi.clicked.connect(self.onar)
        satir.addWidget(self.onar_dugmesi)
        duzen.addLayout(satir)

        self.dugmeleri_kilitle(True)
        self.yardimciyi_baslat()

    # ------------------------------------------------------------------ yetki
    def yardimciyi_baslat(self):
        yol = yardimci_yolu()
        if yol is None:
            self.yaz("HATA: yonetici yardimcisi bulunamadi. Kurulumu tekrarlayin.")
            self.durum.setText("Yardimci betik bulunamadi.")
            return

        self.yaz("Yonetici yetkisi isteniyor (bu islem icin yalnizca bir kez "
                 "sifre sorulur)...")
        try:
            self.surec = subprocess.Popen(
                ["pkexec", yol],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, bufsize=1)
        except FileNotFoundError:
            self.yetki_basarisiz("pkexec bulunamadi. 'sudo apt install pkexec "
                                 "polkitd' ile kurun.")
            return

        self.okuyucu = YardimciOkuyucu(self.surec)
        self.okuyucu.mesaj.connect(self.mesaj_geldi)
        self.okuyucu.kapandi.connect(self.yardimci_kapandi)
        self.okuyucu.start()

    def yetki_basarisiz(self, metin):
        self.surec = None
        self.durum.setText(metin)
        self.yaz(metin)
        self.dugmeleri_kilitle(True)
        self.tara_dugmesi.setText("Yetki Al ve Tara")
        self.tara_dugmesi.setEnabled(True)
        try:
            self.tara_dugmesi.clicked.disconnect()
        except TypeError:
            pass
        self.tara_dugmesi.clicked.connect(self.yeniden_yetki)

    def yeniden_yetki(self):
        self.tara_dugmesi.setEnabled(False)
        try:
            self.tara_dugmesi.clicked.disconnect()
        except TypeError:
            pass
        self.tara_dugmesi.clicked.connect(self.tara)
        self.tara_dugmesi.setText("Yeniden Tara")
        self.yardimciyi_baslat()

    def yardimci_kapandi(self):
        if self.surec is None:
            return
        kod = self.surec.poll()
        if kod == 126 or kod == 127:
            self.yetki_basarisiz("Yetki dogrulamasi iptal edildi. Onarim yapilamaz.")
        else:
            self.yetki_basarisiz("Yonetici baglantisi kapandi.")

    # ------------------------------------------------------------------ iletisim
    def istek(self, nesne):
        if not self.surec or self.surec.poll() is not None:
            self.yaz("Yonetici baglantisi yok.")
            return False
        try:
            self.surec.stdin.write(json.dumps(nesne) + "\n")
            self.surec.stdin.flush()
            return True
        except (BrokenPipeError, ValueError):
            self.yetki_basarisiz("Yonetici baglantisi koptu.")
            return False

    def mesaj_geldi(self, m):
        tur = m.get("tur")
        if tur == "hazir":
            self.durum.setText("Yonetici yetkisi alindi. Bu pencere acik kaldigi "
                               "surece tekrar sifre sorulmayacak.")
            self.yaz("Yetki alindi (yardimci surum %s)." % m.get("surum", "?"))
            self.tara()
        elif tur == "gunluk":
            self.yaz(m.get("metin", ""))
        elif tur == "teshis":
            self.teshis_geldi(m.get("sorunlar", []))
        elif tur == "onarim_bitti":
            self.dugmeleri_kilitle(False)
            self.yaz("=== Onarim tamamlandi ==="
                     if m.get("basarili") else
                     "=== Onarim kismen basarisiz, gunlugu inceleyin ===")
            self.tara()
        elif tur == "hata":
            self.yaz("HATA: %s" % m.get("metin", ""))

    # ------------------------------------------------------------------ arayuz
    def yaz(self, metin):
        self.gunluk.append(metin)

    def dugmeleri_kilitle(self, kilit):
        self.tara_dugmesi.setEnabled(not kilit)
        self.onar_dugmesi.setEnabled(not kilit)

    def tara(self):
        self.agac.clear()
        self.dugmeleri_kilitle(True)
        self.yaz("Tarama basladi...")
        if not self.istek({"komut": "teshis"}):
            self.dugmeleri_kilitle(False)

    def teshis_geldi(self, sorunlar):
        self.sorunlar = sorunlar
        self.agac.clear()
        gercek_sorun = 0
        for s in sorunlar:
            etiket = "Sorun" if s["seviye"] == "sorun" else "Bilgi"
            oge = QTreeWidgetItem([s["baslik"], etiket])
            if s["seviye"] == "sorun":
                gercek_sorun += 1
                oge.setFlags(oge.flags() | Qt.ItemIsUserCheckable)
                oge.setCheckState(0, Qt.Checked if s["onerilen"] else Qt.Unchecked)
            else:
                oge.setFlags(oge.flags() | Qt.ItemIsUserCheckable)
                oge.setCheckState(0, Qt.Unchecked)
            oge.setData(0, Qt.UserRole, s["anahtar"])
            for parca in s["aciklama"].split("\n"):
                oge.addChild(QTreeWidgetItem([parca, ""]))
            self.agac.addTopLevelItem(oge)
        self.agac.expandAll()

        if not sorunlar:
            self.yaz("Sorun bulunamadi. Paket sisteminiz saglikli.")
        else:
            self.yaz("%d bulgu listelendi (%d tanesi onarilmasi gereken sorun)."
                     % (len(sorunlar), gercek_sorun))
        self.dugmeleri_kilitle(False)

    def onar(self):
        gorevler = []
        for i in range(self.agac.topLevelItemCount()):
            oge = self.agac.topLevelItem(i)
            if oge.checkState(0) == Qt.Checked:
                gorevler.append(oge.data(0, Qt.UserRole))
        # bilgi amacli maddeler dogrudan eylem degildir
        gorevler = [g for g in gorevler
                    if g in ("surec_durdur", "dpkg_configure",
                             "apt_fix_broken")]
        if not gorevler:
            QMessageBox.information(self, "Bilgi",
                                    "Onarilacak bir madde isaretlenmedi.")
            return
        onay = QMessageBox.question(
            self, "Onay",
            "Su islemler yapilacak:\n\n- %s\n\nDevam edilsin mi?"
            % "\n- ".join(gorevler),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if onay != QMessageBox.Yes:
            return
        self.dugmeleri_kilitle(True)
        self.istek({"komut": "onar", "gorevler": gorevler})

    def closeEvent(self, olay):
        if self.surec and self.surec.poll() is None:
            try:
                self.surec.stdin.write(json.dumps({"komut": "cikis"}) + "\n")
                self.surec.stdin.flush()
            except (OSError, BrokenPipeError) as e:
                logging.error("AptDoctor stdin yazma hatasi: %s", e)
            try:
                self.surec.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.surec.terminate()
        olay.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pardus APT Doctor")
    pencere = AptDoctor()
    pencere.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
