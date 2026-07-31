#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pardus System Health & Journal Log Doctor
journalctl -p 3 kayitlarini bir Regex kural motoruyla tarar, kritik hatalari
Turkce "neden oldu / nasil cozulur" aciklamalarina cevirir.
Lisans: GPL-3.0
"""
import json
import re
import subprocess
import sys

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QTreeWidget,
                             QTreeWidgetItem, QTextEdit, QMessageBox, QSplitter)

# ---------------------------------------------------------------------------
# Kural motoru: (desen, baslik, neden, cozum)
# ---------------------------------------------------------------------------
KURALLAR = [
    (r"Out of memory: Kill(ed)? process|oom-kill",
     "Bellek yetersizliginden surec sonlandirildi",
     "Cekirdek (kernel) RAM tukendigi icin bir sureci zorla kapatti.",
     "Calisan uygulama sayisini azaltin, swap alanini buyutun ya da "
     "Pardus RAM Guard aracini kullanarak esik uyarisi alin."),
    (r"I/O error|blk_update_request|ata\d+\.\d+: failed command",
     "Disk giris/cikis hatasi",
     "Depolama aygiti okuma/yazma isteklerine yanit veremedi. Kablo, disk "
     "bozulmasi veya USB'nin erken cikarilmasi olabilir.",
     "SMART verisini kontrol edin (smartctl -a /dev/sda), onemli verilerinizi "
     "hemen yedekleyin, disk kablosunu degistirin."),
    (r"segfault at|general protection fault",
     "Uygulama cokmesi (segmentation fault)",
     "Bir program izin verilmeyen bir bellek adresine erismeye calisti; "
     "genelde yazilim hatasi veya bozuk kutuphanedir.",
     "Uygulamayi guncelleyin. Surerse: 'sudo apt install --reinstall <paket>'."),
    (r"Failed to start (.+)\.",
     "Systemd servisi baslatilamadi",
     "Bir sistem servisi acilis sirasinda basarisiz oldu.",
     "'systemctl status <servis>' ile ayrintiya bakin, gerekliyse "
     "'systemctl restart <servis>' deneyin."),
    (r"authentication failure|Failed password for",
     "Basarisiz kimlik dogrulama",
     "Yanlis parola girildi ya da yetkisiz bir erisim denemesi yapildi.",
     "Kendi denemeniz degilse SSH'i kapatin ve parolalarinizi degistirin."),
    (r"No space left on device|ENOSPC",
     "Disk alani doldu",
     "Bolumde bos alan kalmadigi icin yazma islemleri basarisiz oluyor.",
     "'df -h' ile dolu bolumu bulun; apt onbellegini ve eski cekirdekleri "
     "temizleyin (Pardus Cache Cleaner)."),
    (r"nouveau|nvidia|i915|amdgpu.*(error|fail)",
     "Ekran karti surucusu hatasi",
     "Grafik surucusu bir hata bildirdi; ekran donmasi veya siyah ekrana "
     "yol acabilir.",
     "Uygun tescilli/acik surucuyu kurun, cekirdegi guncelleyin."),
    (r"usb \d+-\d+: device descriptor read|device not accepting address",
     "USB aygiti taninamadi",
     "USB cihazi ile iletisim kurulamadi; port, kablo veya guc sorunu.",
     "Baska bir USB portu deneyin, harici disk icin ek guc kaynagi kullanin."),
    (r"Temperature above threshold|thermal.*critical",
     "Islemci asiri isindi",
     "CPU guvenli sicakligin ustune ciktigi icin hiz dusuruldu.",
     "Havalandirmayi temizleyin; Pardus Thermal Guard ile takip edin."),
    (r"Dependency failed for",
     "Bagimli servis baslatilamadi",
     "Bir servis, ihtiyac duydugu baska bir birim baslamadigi icin atlandi.",
     "'systemctl list-dependencies <servis>' ile zinciri inceleyin."),
]

ONEM_ADLARI = {"0": "Acil", "1": "Uyari", "2": "Kritik", "3": "Hata", "4": "Ikaz"}


def journal_oku(oncelik="3", aralik="-1 day"):
    komut = ["journalctl", "-p", oncelik, "-o", "json", "--no-pager",
             "--since", aralik]
    try:
        s = subprocess.run(komut, capture_output=True, text=True, timeout=90)
    except FileNotFoundError:
        return [], "journalctl bulunamadi."
    except subprocess.TimeoutExpired:
        return [], "journalctl zaman asimina ugradi."

    kayitlar = []
    for satir in s.stdout.splitlines():
        try:
            k = json.loads(satir)
        except ValueError:
            continue
        kayitlar.append({
            "mesaj": k.get("MESSAGE", ""),
            "birim": k.get("_SYSTEMD_UNIT") or k.get("SYSLOG_IDENTIFIER") or "?",
            "onem": k.get("PRIORITY", "?"),
            "zaman": k.get("__REALTIME_TIMESTAMP", ""),
        })
    return kayitlar, s.stderr.strip()


def kayit_yorumla(mesaj):
    for desen, baslik, neden, cozum in KURALLAR:
        if re.search(desen, mesaj, re.IGNORECASE):
            return baslik, neden, cozum
    return None


class TaramaIsi(QThread):
    sonuc = pyqtSignal(list, str)

    def __init__(self, oncelik, aralik):
        super().__init__()
        self.oncelik = oncelik
        self.aralik = aralik

    def run(self):
        kayitlar, hata = journal_oku(self.oncelik, self.aralik)
        self.sonuc.emit(kayitlar, hata)


class LogDoctor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pardus Sistem Gunluk Doktoru")
        self.setMinimumSize(940, 620)
        self.kayitlar = []

        duzen = QVBoxLayout(self)
        baslik = QLabel("Sistem Gunlugu Analizi")
        baslik.setStyleSheet("font-size:17px;font-weight:bold;")
        duzen.addWidget(baslik)
        duzen.addWidget(QLabel(
            "Anlasilmaz sistem hatalarini Turkce aciklama ve cozum onerisine cevirir."))

        ust = QHBoxLayout()
        ust.addWidget(QLabel("Onem:"))
        self.onem = QComboBox()
        self.onem.addItem("Kritik ve ustu (p<=2)", "2")
        self.onem.addItem("Hata ve ustu (p<=3)", "3")
        self.onem.addItem("Ikaz ve ustu (p<=4)", "4")
        self.onem.setCurrentIndex(1)
        ust.addWidget(self.onem)
        ust.addWidget(QLabel("Zaman araligi:"))
        self.aralik = QComboBox()
        for etiket, deger in [("Son 1 saat", "-1 hour"), ("Son 24 saat", "-1 day"),
                              ("Son 7 gun", "-7 days"), ("Onceki acilis", "-30 days")]:
            self.aralik.addItem(etiket, deger)
        self.aralik.setCurrentIndex(1)
        ust.addWidget(self.aralik)
        self.tara_dugmesi = QPushButton("Tara")
        self.tara_dugmesi.clicked.connect(self.tara)
        ust.addWidget(self.tara_dugmesi)
        ust.addStretch()
        duzen.addLayout(ust)

        bolucu = QSplitter(Qt.Vertical)
        self.agac = QTreeWidget()
        self.agac.setHeaderLabels(["Sorun", "Birim", "Adet"])
        self.agac.itemSelectionChanged.connect(self.detay_goster)
        bolucu.addWidget(self.agac)

        self.detay = QTextEdit()
        self.detay.setReadOnly(True)
        bolucu.addWidget(self.detay)
        bolucu.setSizes([380, 220])
        duzen.addWidget(bolucu)

        alt = QHBoxLayout()
        b = QPushButton("Raporu Kaydet")
        b.clicked.connect(self.rapor_kaydet)
        alt.addWidget(b)
        alt.addStretch()
        duzen.addLayout(alt)

        self.tara()

    def tara(self):
        self.tara_dugmesi.setEnabled(False)
        self.agac.clear()
        self.detay.setPlainText("Gunlukler okunuyor, lutfen bekleyin...")
        self.isci = TaramaIsi(self.onem.currentData(), self.aralik.currentData())
        self.isci.sonuc.connect(self.sonuc_geldi)
        self.isci.start()

    def sonuc_geldi(self, kayitlar, hata):
        self.tara_dugmesi.setEnabled(True)
        self.kayitlar = kayitlar
        if hata:
            self.detay.setPlainText(hata)
        if not kayitlar:
            self.detay.setPlainText("Secilen aralikta bu onem seviyesinde kayit yok. "
                                    "Sisteminiz temiz gorunuyor.")
            return

        gruplar = {}
        yorumsuz = []
        for k in kayitlar:
            yorum = kayit_yorumla(k["mesaj"])
            if yorum is None:
                yorumsuz.append(k)
                continue
            gruplar.setdefault(yorum, []).append(k)

        for (b, neden, cozum), liste in sorted(gruplar.items(),
                                               key=lambda x: -len(x[1])):
            birimler = sorted({k["birim"] for k in liste})
            ust = QTreeWidgetItem([b, ", ".join(birimler[:2]), str(len(liste))])
            ust.setData(0, Qt.UserRole, (b, neden, cozum, liste))
            for k in liste[:20]:
                alt = QTreeWidgetItem([k["mesaj"][:120], k["birim"], ""])
                ust.addChild(alt)
            self.agac.addTopLevelItem(ust)

        if yorumsuz:
            ust = QTreeWidgetItem(["Siniflandirilamayan kayitlar", "-", str(len(yorumsuz))])
            ust.setData(0, Qt.UserRole,
                        ("Siniflandirilamayan kayitlar",
                         "Bu kayitlar kural veritabaninda tanimli degil.",
                         "Mesaji internette aratin ya da yeni bir kural ekleyin.",
                         yorumsuz))
            for k in yorumsuz[:30]:
                ust.addChild(QTreeWidgetItem([k["mesaj"][:120], k["birim"], ""]))
            self.agac.addTopLevelItem(ust)

        self.detay.setPlainText(
            "%d kayit incelendi, %d farkli sorun turu bulundu.\n"
            "Ayrintiyi gormek icin listeden bir baslik secin."
            % (len(kayitlar), len(gruplar)))

    def detay_goster(self):
        ogeler = self.agac.selectedItems()
        if not ogeler:
            return
        oge = ogeler[0]
        veri = oge.data(0, Qt.UserRole)
        if veri is None and oge.parent() is not None:
            veri = oge.parent().data(0, Qt.UserRole)
        if veri is None:
            return
        baslik, neden, cozum, liste = veri
        self.detay.setPlainText(
            "SORUN: %s\n\nNEDEN OLDU?\n%s\n\nNASIL COZULUR?\n%s\n\n"
            "ORNEK KAYIT:\n%s\n\nTOPLAM: %d kayit"
            % (baslik, neden, cozum, liste[0]["mesaj"], len(liste)))

    def rapor_kaydet(self):
        import os
        yol = os.path.expanduser("~/pardus-log-raporu.txt")
        with open(yol, "w") as f:
            f.write("Pardus Sistem Gunluk Raporu\n\n")
            for i in range(self.agac.topLevelItemCount()):
                oge = self.agac.topLevelItem(i)
                baslik, neden, cozum, liste = oge.data(0, Qt.UserRole)
                f.write("== %s (%d kayit)\nNeden: %s\nCozum: %s\n\n"
                        % (baslik, len(liste), neden, cozum))
        QMessageBox.information(self, "Kaydedildi", "Rapor: %s" % yol)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pardus Log Doctor")
    p = LogDoctor()
    p.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
