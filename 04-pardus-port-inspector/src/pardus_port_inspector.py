#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pardus Rogue Socket & Port Inspector
Acik TCP/UDP portlarini, dinleyen ve disariya baglanan surecleri gorsel
olarak listeler; supheli bulunan portlari ufw ile kapatir.
Lisans: GPL-3.0
"""
import os
import sys

import psutil
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QCheckBox,
                             QLineEdit, QMessageBox, QTextEdit)
import subprocess

# DIKKAT: 0.0.0.0 ve :: "yerel" DEGILDIR - tum ag arayuzlerinde dinlemek
# anlamina gelir, yani en genis erisim. Yalnizca loopback gercekten yereldir.
LOOPBACK_ADRESLER = {"::1"}
TUM_ARAYUZLER = {"0.0.0.0", "::"}


def disa_acik_mi(ip):
    """Soketin makine disindan erisilebilir olup olmadigini soyler."""
    if ip in TUM_ARAYUZLER:
        return True
    if ip in LOOPBACK_ADRESLER or ip.startswith("127."):
        return False
    return True

# Yaygin ve genelde masumsuz servisler
BILINEN_PORTLAR = {
    22: "SSH", 53: "DNS", 80: "HTTP", 443: "HTTPS", 631: "CUPS yazici",
    5353: "mDNS/Avahi", 68: "DHCP istemci", 123: "NTP", 25: "SMTP",
    3306: "MySQL", 5432: "PostgreSQL", 139: "NetBIOS", 445: "SMB",
}

# Gecmiste arka kapi olarak kullanilmis / dikkat cekici portlar
SUPHELI_PORTLAR = {
    23: "Telnet - sifreler duz metin gider",
    1080: "SOCKS vekil sunucu",
    4444: "Sik kullanilan ters kabuk portu",
    5555: "ADB / uzaktan erisim",
    6667: "IRC - botnet iletisimi",
    31337: "Klasik arka kapi portu",
}


def okunabilir_adres(adres):
    if not adres:
        return "-"
    return "%s:%s" % (adres.ip, adres.port)


def baglantilari_al():
    satirlar = []
    try:
        baglantilar = psutil.net_connections(kind="inet")
    except psutil.AccessDenied:
        return None
    for b in baglantilar:
        try:
            surec = psutil.Process(b.pid).name() if b.pid else "?"
            kullanici = psutil.Process(b.pid).username() if b.pid else "?"
            yol = psutil.Process(b.pid).exe() if b.pid else ""
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            surec, kullanici, yol = "?", "?", ""
        protokol = "TCP" if b.type == 1 else "UDP"
        satirlar.append({
            "protokol": protokol,
            "yerel": okunabilir_adres(b.laddr),
            "uzak": okunabilir_adres(b.raddr),
            "durum": b.status,
            "pid": b.pid or 0,
            "surec": surec,
            "kullanici": kullanici,
            "yol": yol,
            "port": b.laddr.port if b.laddr else 0,
            "disa_acik": bool(b.laddr and disa_acik_mi(b.laddr.ip)),
            "tum_arayuzler": bool(b.laddr and b.laddr.ip in TUM_ARAYUZLER),
        })
    return satirlar


def risk_degerlendir(satir):
    """(seviye, aciklama) dondurur. seviye: 0 normal, 1 dikkat, 2 supheli"""
    port = satir["port"]

    # 1) Gecici dizinden calisan ag sureci her durumda en yuksek risk
    if satir.get("yol", "").startswith(("/tmp", "/dev/shm", "/var/tmp")):
        return 2, "Gecici dizinden calisan bir surec ag kullaniyor"

    # 2) Bilinen arka kapi / riskli portlar
    if port in SUPHELI_PORTLAR:
        return 2, SUPHELI_PORTLAR[port]

    if satir["durum"] == "LISTEN":
        if satir["disa_acik"]:
            nerede = ("tum arayuzlerde (0.0.0.0)" if satir.get("tum_arayuzler")
                      else "dis arayuzde")
            ad = BILINEN_PORTLAR.get(port)
            if ad:
                return 1, "%s servisi %s dinliyor - aga acik" % (ad, nerede)
            return 2, "Tanimsiz servis %s dinliyor - aga acik" % nerede
        return 0, "Yalnizca bu makineden erisilebilir (loopback)"

    if satir["durum"] == "ESTABLISHED" and satir["uzak"] != "-":
        return 0, "Kurulu baglanti"
    return 0, ""


def ufw_durumu():
    try:
        s = subprocess.run(["ufw", "status"], capture_output=True, text=True, timeout=10)
        return s.stdout.strip() or s.stderr.strip()
    except Exception as h:
        return "ufw sorgulanamadi: %s" % h


class PortInspector(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pardus Port ve Baglanti Denetleyicisi")
        self.setMinimumSize(980, 600)
        self.satirlar = []

        duzen = QVBoxLayout(self)
        baslik = QLabel("Acik Portlar ve Ag Baglantilari")
        baslik.setStyleSheet("font-size:17px;font-weight:bold;")
        duzen.addWidget(baslik)

        ust = QHBoxLayout()
        self.sadece_dinleyen = QCheckBox("Sadece dinleyen (LISTEN) portlar")
        self.sadece_dinleyen.setChecked(True)
        self.sadece_dinleyen.stateChanged.connect(self.tabloyu_doldur)
        ust.addWidget(self.sadece_dinleyen)
        self.sadece_supheli = QCheckBox("Sadece supheli olanlar")
        self.sadece_supheli.stateChanged.connect(self.tabloyu_doldur)
        ust.addWidget(self.sadece_supheli)
        ust.addWidget(QLabel("Filtre:"))
        self.filtre = QLineEdit()
        self.filtre.setPlaceholderText("surec adi veya port")
        self.filtre.textChanged.connect(self.tabloyu_doldur)
        ust.addWidget(self.filtre)
        duzen.addLayout(ust)

        self.tablo = QTableWidget(0, 8)
        self.tablo.setHorizontalHeaderLabels(
            ["Protokol", "Yerel adres", "Uzak adres", "Durum",
             "PID", "Surec", "Kullanici", "Degerlendirme"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tablo.horizontalHeader().setStretchLastSection(True)
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        duzen.addWidget(self.tablo)

        self.ufw_kutusu = QTextEdit()
        self.ufw_kutusu.setReadOnly(True)
        self.ufw_kutusu.setMaximumHeight(120)
        self.ufw_kutusu.setStyleSheet("font-family: monospace;")
        duzen.addWidget(QLabel("Guvenlik duvari (ufw) durumu:"))
        duzen.addWidget(self.ufw_kutusu)

        alt = QHBoxLayout()
        b1 = QPushButton("Yenile")
        b1.clicked.connect(self.yenile)
        alt.addWidget(b1)
        b2 = QPushButton("Secili Portu ufw ile Kapat")
        b2.clicked.connect(self.portu_kapat)
        alt.addWidget(b2)
        b3 = QPushButton("Guvenlik Duvarini Etkinlestir")
        b3.clicked.connect(self.ufw_etkinlestir)
        alt.addWidget(b3)
        b4 = QPushButton("Raporu Kaydet")
        b4.clicked.connect(self.rapor_kaydet)
        alt.addWidget(b4)
        duzen.addLayout(alt)

        self.yenile()
        self.zamanlayici = QTimer()
        self.zamanlayici.timeout.connect(self.yenile)
        self.zamanlayici.start(10000)

    def yenile(self):
        veri = baglantilari_al()
        if veri is None:
            QMessageBox.warning(self, "Yetki",
                                "Baglantilari gormek icin yeterli yetki yok. "
                                "Uygulamayi 'pkexec' ile calistirin.")
            return
        self.satirlar = veri
        self.tabloyu_doldur()
        self.ufw_kutusu.setPlainText(ufw_durumu())

    def gorunur_satirlar(self):
        metin = self.filtre.text().strip().lower()
        cikti = []
        for s in self.satirlar:
            if self.sadece_dinleyen.isChecked() and s["durum"] != "LISTEN":
                continue
            seviye, aciklama = risk_degerlendir(s)
            if self.sadece_supheli.isChecked() and seviye < 2:
                continue
            if metin and metin not in s["surec"].lower() and metin not in str(s["port"]):
                continue
            cikti.append((s, seviye, aciklama))
        return cikti

    def tabloyu_doldur(self):
        veri = self.gorunur_satirlar()
        self.tablo.setRowCount(len(veri))
        for i, (s, seviye, aciklama) in enumerate(veri):
            hucreler = [s["protokol"], s["yerel"], s["uzak"], s["durum"],
                        str(s["pid"]), s["surec"], s["kullanici"], aciklama]
            for j, deger in enumerate(hucreler):
                oge = QTableWidgetItem(deger)
                if seviye == 2:
                    oge.setBackground(QColor("#f8d7da"))
                elif seviye == 1:
                    oge.setBackground(QColor("#fff3cd"))
                self.tablo.setItem(i, j, oge)

    def secili_port(self):
        satir = self.tablo.currentRow()
        if satir < 0:
            return None, None
        veri = self.gorunur_satirlar()
        if satir >= len(veri):
            return None, None
        s = veri[satir][0]
        return s["port"], s["protokol"].lower()

    def portu_kapat(self):
        port, protokol = self.secili_port()
        if port is None:
            QMessageBox.information(self, "Bilgi", "Once tablodan bir satir secin.")
            return
        onay = QMessageBox.question(
            self, "Onay",
            "%d/%s portuna disaridan erisim ufw ile engellensin mi?\n"
            "(Kural: ufw deny %d/%s)" % (port, protokol, port, protokol),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if onay != QMessageBox.Yes:
            return
        s = subprocess.run(["pkexec", "ufw", "deny", "%d/%s" % (port, protokol)],
                           capture_output=True, text=True)
        QMessageBox.information(self, "Sonuc", s.stdout.strip() or s.stderr.strip())
        self.yenile()

    def ufw_etkinlestir(self):
        s = subprocess.run(["pkexec", "ufw", "--force", "enable"],
                           capture_output=True, text=True)
        QMessageBox.information(self, "Sonuc", s.stdout.strip() or s.stderr.strip())
        self.yenile()

    def rapor_kaydet(self):
        yol = os.path.expanduser("~/pardus-port-raporu.txt")
        with open(yol, "w") as f:
            f.write("Pardus Port Denetim Raporu\n\n")
            for s in self.satirlar:
                seviye, aciklama = risk_degerlendir(s)
                f.write("[%s] %s %s -> %s | %s (PID %s) | %s\n"
                        % ("SUPHELI" if seviye == 2 else "DIKKAT" if seviye == 1 else "NORMAL",
                           s["protokol"], s["yerel"], s["uzak"], s["surec"], s["pid"], aciklama))
        QMessageBox.information(self, "Kaydedildi", "Rapor: %s" % yol)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pardus Port Inspector")
    p = PortInspector()
    p.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
