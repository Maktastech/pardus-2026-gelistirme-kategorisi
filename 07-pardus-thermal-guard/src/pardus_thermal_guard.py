#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pardus Thermal Throttling Guard
/sys/class/thermal ve cpufreq verilerini okuyarak islemci sicakligini ve
frekans kisitlamasini (thermal throttling) sistem tepsisinden bildirir.
Lisans: GPL-3.0
"""
import glob
import os
import sys

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import (QIcon, QPixmap, QPainter, QColor, QBrush, QPen)
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction,
                             QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QProgressBar, QTableWidget, QTableWidgetItem,
                             QHeaderView, QSpinBox, QAbstractItemView)

UYARI_SICAKLIK = 80.0
KRITIK_SICAKLIK = 90.0
YENILEME_MS = 3000


def ikon_ciz(seviye):
    """Tema bagimsiz termometre simgesi. Pardus 25 "Bilge" ikon setinde bir
    isim bulunamazsa QIcon.fromTheme bos ikon dondurur ve tepsi simgesi hic
    gorunmez; bu yuzden ikon kodla ciziliyor.
    seviye: 'normal' | 'uyari' | 'kritik' | 'yok'"""
    renk = {"normal": QColor("#27ae60"),
            "uyari": QColor("#e67e22"),
            "kritik": QColor("#c0392b"),
            "yok": QColor("#7f8c8d")}[seviye]
    dolu = {"normal": 14, "uyari": 24, "kritik": 32, "yok": 6}[seviye]
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    # termometre govdesi
    p.setPen(QPen(QColor(0, 0, 0, 90), 2))
    p.setBrush(QBrush(QColor("#ecf0f1")))
    p.drawRoundedRect(26, 6, 14, 40, 7, 7)
    p.drawEllipse(20, 40, 26, 20)
    # civa
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(renk))
    p.drawEllipse(25, 44, 16, 14)
    p.drawRoundedRect(30, 42 - dolu, 6, dolu + 6, 3, 3)
    # olcek cizgileri
    p.setPen(QPen(QColor(0, 0, 0, 120), 2))
    for y in (14, 22, 30, 38):
        p.drawLine(41, y, 47, y)
    p.end()
    return QIcon(pm)


def tanilama():
    app = QApplication(sys.argv)
    print("=" * 58)
    print(" Pardus Thermal Guard - Tanilama")
    print("=" * 58)
    print("Sistem tepsisi mevcut mu : %s"
          % ("EVET" if QSystemTrayIcon.isSystemTrayAvailable() else "HAYIR"))
    print("Tema ikonu bulundu mu    : %s"
          % ("EVET" if not QIcon.fromTheme("sensors-temperature").isNull()
             else "HAYIR (kendi ikonumuz kullanilacak)"))
    print("Cizilen ikon gecerli mi  : %s"
          % ("EVET" if not ikon_ciz("normal").isNull() else "HAYIR"))
    print()
    bolgeler = termal_bolgeler()
    if not bolgeler:
        print("Termal bolge bulunamadi (/sys/class/thermal bos).")
        print("  -> Sanal makinelerde sicaklik sensoru genelde YOKTUR.")
        print("     Bu arac fiziksel bir makinede test edilmelidir.")
    else:
        print("Termal bolgeler:")
        for b in bolgeler:
            print("   %-20s %.1f C" % (b["ad"], b["sicaklik"]))
        print("CPU sicakligi olarak secilen: %.1f C" % cpu_sicakligi(bolgeler))
    print()
    frekanslar = cpu_frekanslari()
    if not frekanslar:
        print("cpufreq verisi yok (/sys/devices/system/cpu/*/cpufreq bulunamadi).")
        print("  -> Sanal makinelerde frekans olceklendirme genelde kapalidir.")
    else:
        print("Cekirdek frekanslari:")
        for f in frekanslar[:8]:
            print("   %-8s %6.0f / %6.0f MHz  (%s)"
                  % (f["cekirdek"], f["simdi_mhz"], f["azami_mhz"], f["yonetici"]))
    print()
    print("Donanimsal hiz kisitlama sayaci: %d" % kisitlama_sayaci())
    print("=" * 58)
    return 0


def _oku(yol):
    try:
        with open(yol, "r") as f:
            return f.read().strip()
    except OSError:
        return None


def termal_bolgeler():
    bolgeler = []
    for dizin in sorted(glob.glob("/sys/class/thermal/thermal_zone*")):
        ham = _oku(os.path.join(dizin, "temp"))
        tur = _oku(os.path.join(dizin, "type")) or os.path.basename(dizin)
        if ham is None:
            continue
        try:
            sicaklik = int(ham) / 1000.0
        except ValueError:
            continue
        bolgeler.append({"ad": tur, "sicaklik": sicaklik})
    return bolgeler


def cpu_sicakligi(bolgeler):
    for b in bolgeler:
        if b["ad"] in ("x86_pkg_temp", "cpu-thermal", "coretemp", "k10temp",
                       "acpitz", "soc_thermal"):
            return b["sicaklik"]
    return max((b["sicaklik"] for b in bolgeler), default=None)


def cpu_frekanslari():
    veriler = []
    for dizin in sorted(glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq")):
        cekirdek = dizin.split("/cpu")[1].split("/")[0]
        simdi = _oku(os.path.join(dizin, "scaling_cur_freq"))
        azami = _oku(os.path.join(dizin, "cpuinfo_max_freq"))
        yonetici = _oku(os.path.join(dizin, "scaling_governor")) or "-"
        if simdi is None or azami is None:
            continue
        try:
            simdi, azami = int(simdi), int(azami)
        except ValueError:
            continue
        veriler.append({
            "cekirdek": "CPU%s" % cekirdek,
            "simdi_mhz": simdi / 1000.0,
            "azami_mhz": azami / 1000.0,
            "oran": 100.0 * simdi / azami if azami else 0,
            "yonetici": yonetici,
        })
    return veriler


def kisitlama_sayaci():
    """Intel islemcilerde donanimsal throttling sayaci."""
    toplam = 0
    for yol in glob.glob("/sys/devices/system/cpu/cpu*/thermal_throttle/core_throttle_count"):
        deger = _oku(yol)
        if deger and deger.isdigit():
            toplam += int(deger)
    return toplam


class ThermalPenceresi(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pardus Sicaklik ve Frekans Izleyici")
        self.setMinimumSize(620, 500)
        duzen = QVBoxLayout(self)

        self.baslik = QLabel("Sicaklik olculuyor...")
        self.baslik.setStyleSheet("font-size:16px;font-weight:bold;")
        duzen.addWidget(self.baslik)

        self.sicaklik_cubuk = QProgressBar()
        self.sicaklik_cubuk.setRange(0, 110)
        duzen.addWidget(self.sicaklik_cubuk)

        esik_satiri = QHBoxLayout()
        esik_satiri.addWidget(QLabel("Uyari esigi (C):"))
        self.uyari_kutusu = QSpinBox()
        self.uyari_kutusu.setRange(50, 105)
        self.uyari_kutusu.setValue(int(UYARI_SICAKLIK))
        esik_satiri.addWidget(self.uyari_kutusu)
        esik_satiri.addStretch()
        duzen.addLayout(esik_satiri)

        duzen.addWidget(QLabel("Termal bolgeler:"))
        self.bolge_tablosu = QTableWidget(0, 2)
        self.bolge_tablosu.setHorizontalHeaderLabels(["Bolge", "Sicaklik"])
        self.bolge_tablosu.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bolge_tablosu.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.bolge_tablosu.setMaximumHeight(140)
        duzen.addWidget(self.bolge_tablosu)

        duzen.addWidget(QLabel("Cekirdek frekanslari:"))
        self.frekans_tablosu = QTableWidget(0, 4)
        self.frekans_tablosu.setHorizontalHeaderLabels(
            ["Cekirdek", "Anlik (MHz)", "Azami (MHz)", "Yonetici"])
        self.frekans_tablosu.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.frekans_tablosu.setEditTriggers(QAbstractItemView.NoEditTriggers)
        duzen.addWidget(self.frekans_tablosu)

        self.kisit_etiketi = QLabel("")
        duzen.addWidget(self.kisit_etiketi)

    def guncelle(self, bolgeler, frekanslar, kisit, cpu_sic):
        if cpu_sic is None:
            self.baslik.setText("Sicaklik sensoru bulunamadi (sanal makine olabilir).")
            return

        uyari = self.uyari_kutusu.value()
        self.sicaklik_cubuk.setValue(int(cpu_sic))
        self.sicaklik_cubuk.setFormat("%.1f C" % cpu_sic)
        if cpu_sic >= KRITIK_SICAKLIK:
            self.baslik.setText("KRITIK: Islemci asiri isindi (%.1f C)" % cpu_sic)
            renk = "#c0392b"
        elif cpu_sic >= uyari:
            self.baslik.setText("Uyari: Sicaklik yuksek (%.1f C)" % cpu_sic)
            renk = "#e67e22"
        else:
            self.baslik.setText("Sicaklik normal (%.1f C)" % cpu_sic)
            renk = "#27ae60"
        self.baslik.setStyleSheet("font-size:16px;font-weight:bold;color:%s;" % renk)

        self.bolge_tablosu.setRowCount(len(bolgeler))
        for i, b in enumerate(bolgeler):
            self.bolge_tablosu.setItem(i, 0, QTableWidgetItem(b["ad"]))
            self.bolge_tablosu.setItem(i, 1, QTableWidgetItem("%.1f C" % b["sicaklik"]))

        self.frekans_tablosu.setRowCount(len(frekanslar))
        for i, f in enumerate(frekanslar):
            for j, deger in enumerate([f["cekirdek"], "%.0f" % f["simdi_mhz"],
                                       "%.0f" % f["azami_mhz"], f["yonetici"]]):
                self.frekans_tablosu.setItem(i, j, QTableWidgetItem(deger))

        if kisit > 0:
            self.kisit_etiketi.setText(
                "Donanimsal hiz kisitlamasi sayaci: %d\n"
                "Islemci isinma nedeniyle en az bir kez yavaslatilmis. "
                "Havalandirmayi temizlemeniz onerilir." % kisit)
            self.kisit_etiketi.setStyleSheet("color:#c0392b;")
        else:
            self.kisit_etiketi.setText("Donanimsal hiz kisitlamasi tespit edilmedi.")
            self.kisit_etiketi.setStyleSheet("color:#27ae60;")


class ThermalGuard:
    def __init__(self, app):
        self.app = app
        self.pencere = ThermalPenceresi()
        self.uyarildi = False

        self.tepsi = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tepsi = QSystemTrayIcon(ikon_ciz("normal"))
            menu = QMenu()
            a1 = QAction("Pencereyi Goster", menu)
            a1.triggered.connect(self.pencere_goster)
            menu.addAction(a1)
            menu.addSeparator()
            a2 = QAction("Cikis", menu)
            a2.triggered.connect(app.quit)
            menu.addAction(a2)
            self.tepsi.setContextMenu(menu)
            self.tepsi.activated.connect(
                lambda s: self.pencere_goster() if s == QSystemTrayIcon.Trigger else None)
            self.tepsi.setToolTip("Pardus Thermal Guard")
            self.tepsi.show()
        else:
            print("[thermal-guard] UYARI: sistem tepsisi yok, pencere modunda "
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

    def tik(self):
        bolgeler = termal_bolgeler()
        frekanslar = cpu_frekanslari()
        kisit = kisitlama_sayaci()
        sic = cpu_sicakligi(bolgeler)
        self.pencere.guncelle(bolgeler, frekanslar, kisit, sic)

        if sic is None:
            if self.tepsi is not None:
                self.tepsi.setIcon(ikon_ciz("yok"))
                self.tepsi.setToolTip("Sicaklik sensoru yok")
            return

        uyari = self.pencere.uyari_kutusu.value()
        seviye = ("kritik" if sic >= KRITIK_SICAKLIK
                  else "uyari" if sic >= uyari else "normal")
        if self.tepsi is not None:
            self.tepsi.setIcon(ikon_ciz(seviye))
            self.tepsi.setToolTip("CPU: %.1f C" % sic)

        if sic >= uyari:
            if not self.uyarildi:
                metin = ("Sicaklik %.1f C. Performans dusebilir; havalandirmayi "
                         "kontrol edin." % sic)
                if self.tepsi is not None:
                    self.tepsi.showMessage("Islemci isiniyor", metin,
                                           QSystemTrayIcon.Warning, 6000)
                else:
                    print("[thermal-guard] UYARI: %s" % metin, flush=True)
                self.uyarildi = True
        elif sic < uyari - 5:
            self.uyarildi = False


def main():
    if "--tani" in sys.argv:
        sys.exit(tanilama())
    app = QApplication(sys.argv)
    app.setApplicationName("Pardus Thermal Guard")
    app.setWindowIcon(ikon_ciz("normal"))
    app.setQuitOnLastWindowClosed(False)
    ThermalGuard(app)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
