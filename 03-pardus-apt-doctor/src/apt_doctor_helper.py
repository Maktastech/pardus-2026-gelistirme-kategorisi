#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pardus APT Doctor - yonetici yardimcisi (root helper)  v2.0

Arayuz bu betigi acilista BIR KEZ pkexec ile baslatir; sonraki tum islemler
stdin/stdout uzerinden JSON satirlariyla yapilir, tekrar sifre sorulmaz.

TASARIM NOTU (v2.0'da degisti):
  /var/lib/dpkg/lock ve benzeri dosyalar her Debian/Pardus sisteminde HER ZAMAN
  vardir; varliklari bir hata degildir. Onemli olan dosyanin fcntl ile gercekten
  KILITLI olup olmadigidir. Bu yuzden bu arac kilit dosyasi SILMEZ. Kilit
  tutuluyorsa tutan surec bulunur ve durdurulmasi onerilir; asil onarim
  'dpkg --configure -a' ve 'apt-get install -f' ile yapilir.

Protokol:
  Gelen : {"komut": "teshis"} | {"komut": "onar", "gorevler": [...]} | {"komut": "cikis"}
  Giden : {"tur": "hazir"|"gunluk"|"teshis"|"onarim_bitti"|"hata", ...}
Lisans: GPL-3.0
"""
import fcntl
import json
import os
import re
import subprocess
import sys
import time

SURUM = "2.0"

KILIT_DOSYALARI = [
    ("/var/lib/dpkg/lock", "dpkg ana kilidi"),
    ("/var/lib/dpkg/lock-frontend", "dpkg on yuz kilidi"),
    ("/var/lib/apt/lists/lock", "apt paket listesi kilidi"),
    ("/var/cache/apt/archives/lock", "apt indirme onbellegi kilidi"),
]

PAKET_YONETICILERI = {
    "apt": "apt",
    "apt-get": "apt-get",
    "aptitude": "aptitude",
    "dpkg": "dpkg",
    "synaptic": "Synaptic",
    "unattended-upgr": "Otomatik guncelleme",
    "packagekitd": "PackageKit (Yazilim Merkezi arka plani)",
    "gnome-software": "Yazilim Merkezi",
    "pardus-software": "Pardus Yazilim Merkezi",
    "appstreamcli": "AppStream",
}

SERVIS_ESLEMESI = {
    "packagekitd": "packagekit",
    "unattended-upgr": "unattended-upgrades",
}


def yaz(nesne):
    sys.stdout.write(json.dumps(nesne, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def gunluk(metin):
    yaz({"tur": "gunluk", "metin": metin})


def komut(args, zaman_asimi=1800):
    try:
        s = subprocess.run(args, capture_output=True, text=True, timeout=zaman_asimi)
        return s.returncode, ((s.stdout or "") + (s.stderr or "")).strip()
    except FileNotFoundError:
        return 127, "Komut bulunamadi: %s" % args[0]
    except subprocess.TimeoutExpired:
        return 124, "Zaman asimi: %s" % " ".join(args)


# ---------------------------------------------------------------- kilit testi
def kilit_durumu(yol):
    """Dosyanin gercekten kilitli olup olmadigini test eder.
    apt/dpkg POSIX kayit kilidi (fcntl F_SETLK) kullanir; lockf tam bunu test eder.
    Kilidi aninda birakir, sisteme mudahale etmez.
    Doner: True (kilitli) | False (serbest) | None (dosya yok / test edilemedi)"""
    if not os.path.exists(yol):
        return None
    try:
        fd = os.open(yol, os.O_RDWR)
    except OSError:
        return None
    try:
        fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.lockf(fd, fcntl.LOCK_UN)
        return False
    except OSError:
        return True
    finally:
        os.close(fd)


def dosyayi_acan_pidler(yol):
    """/proc/<pid>/fd taramasi. root olarak calistigi icin butun surecleri gorur."""
    acanlar = []
    try:
        hedef = os.path.realpath(yol)
    except OSError:
        hedef = yol
    for girdi in os.listdir("/proc"):
        if not girdi.isdigit():
            continue
        fd_dizini = "/proc/%s/fd" % girdi
        try:
            fdler = os.listdir(fd_dizini)
        except OSError:
            continue
        for fd in fdler:
            try:
                if os.readlink(os.path.join(fd_dizini, fd)) == hedef:
                    acanlar.append(int(girdi))
                    break
            except OSError:
                continue
    return acanlar


def surec_adi(pid):
    try:
        with open("/proc/%d/comm" % pid) as f:
            return f.read().strip()
    except OSError:
        return "?"


def calisan_paket_yoneticileri():
    bulunan = []
    for girdi in os.listdir("/proc"):
        if not girdi.isdigit():
            continue
        ad = surec_adi(int(girdi))
        if ad in PAKET_YONETICILERI:
            bulunan.append((int(girdi), ad))
    return bulunan


# -------------------------------------------------------------------- teshis
def teshis():
    sorunlar = []

    kilitli = []
    for yol, aciklama in KILIT_DOSYALARI:
        if kilit_durumu(yol) is True:
            acanlar = [(p, surec_adi(p)) for p in dosyayi_acan_pidler(yol)]
            kilitli.append((yol, aciklama, acanlar))

    calisanlar = calisan_paket_yoneticileri()

    if kilitli:
        satirlar = []
        for yol, aciklama, acanlar in kilitli:
            tutan = (", ".join("%s (PID %d)" % (a, p) for p, a in acanlar)
                     if acanlar else "belirlenemedi")
            satirlar.append("  %s (%s)\n    tutan: %s" % (yol, aciklama, tutan))
        sorunlar.append({
            "anahtar": "kilit_mesgul",
            "baslik": "Paket sistemi kilidi baska bir islem tarafindan tutuluyor",
            "aciklama": ("Su an bir paket islemi surdugu icin apt/dpkg kilitli:\n"
                         + "\n".join(satirlar) +
                         "\n\nBu arac kilit dosyalarini SILMEZ; silmek paket "
                         "veritabanini bozar. Dogru cozum kilidi tutan islemin "
                         "bitmesini beklemek ya da asagidaki 'Paket yoneticisi "
                         "servisini durdur' maddesini isaretlemektir."),
            "seviye": "sorun",
            "onerilen": False,
        })
    else:
        sorunlar.append({
            "anahtar": "kilit_serbest",
            "baslik": "Paket sistemi kilidi serbest",
            "aciklama": ("Kilit dosyalari mevcut ama hicbiri tutulmuyor; bu NORMAL "
                         "durumdur. Kilit dosyalarinin diskte bulunmasi bir hata "
                         "degildir, her Pardus kurulumunda vardir."),
            "seviye": "bilgi",
            "onerilen": False,
        })

    if calisanlar:
        metin = ", ".join("%s (PID %d)" % (PAKET_YONETICILERI[a], p)
                          for p, a in calisanlar)
        sorunlar.append({
            "anahtar": "surec_durdur",
            "baslik": "Paket yoneticisi servisini durdur",
            "aciklama": ("Calisan surecler: %s\n"
                         "PackageKit'in arka planda calismasi NORMALDIR ve tek "
                         "basina bir sorun degildir. Yalnizca yukarida kilit "
                         "mesgul gorunuyorsa ve bir kurulum beklemiyorsaniz bu "
                         "maddeyi isaretleyin. Surecler 'kill' ile degil "
                         "'systemctl stop' ile nazikce durdurulur." % metin),
            "seviye": "bilgi",
            "onerilen": False,
        })

    kod, cikti = komut(["dpkg", "--audit"], 180)
    # 127/124: komut yok veya zaman asimi -> bulgu degil, ortam sorunu
    if kod not in (127, 124) and cikti.strip():
        sorunlar.append({
            "anahtar": "dpkg_configure",
            "baslik": "Yarim kalmis paket kurulumu",
            "aciklama": ("dpkg bazi paketlerin yapilandirilmadigini bildiriyor:\n"
                         + cikti.strip()[:900] +
                         "\n\nUygulanacak komut: dpkg --configure -a"),
            "seviye": "sorun",
            "onerilen": True,
        })

    kod, cikti = komut(["apt-get", "-s", "check"], 180)
    if kod in (127, 124):
        sorunlar.append({
            "anahtar": "ortam_hatasi",
            "baslik": "apt-get calistirilamadi",
            "aciklama": "Teshis yapilamadi: " + cikti[:300],
            "seviye": "bilgi",
            "onerilen": False,
        })
    elif kod != 0 or re.search(r"kirik|broken|unmet", cikti, re.IGNORECASE):
        sorunlar.append({
            "anahtar": "apt_fix_broken",
            "baslik": "Karsilanmamis bagimlilik",
            "aciklama": ("Paket veritabaninda kirik bagimliliklar var:\n"
                         + cikti.strip()[:900] +
                         "\n\nUygulanacak komut: apt-get install -f"),
            "seviye": "sorun",
            "onerilen": True,
        })

    return sorunlar


# -------------------------------------------------------------------- onarim
def surecleri_durdur():
    basarili = True
    calisanlar = calisan_paket_yoneticileri()
    if not calisanlar:
        gunluk("    Durdurulacak paket yoneticisi yok.")
        return True
    for pid, ad in calisanlar:
        birim = SERVIS_ESLEMESI.get(ad)
        if birim:
            gunluk("    systemctl stop %s" % birim)
            kod, cikti = komut(["systemctl", "stop", birim], 90)
        else:
            gunluk("    %s (PID %d) icin TERM sinyali" % (ad, pid))
            kod, cikti = komut(["kill", "-TERM", str(pid)], 30)
        if kod != 0:
            gunluk("      HATA: %s" % cikti)
            basarili = False
    time.sleep(2)

    kalan = calisan_paket_yoneticileri()
    if kalan:
        gunluk("    Hala calisan: %s" % ", ".join(a for _, a in kalan))
    else:
        gunluk("    Tum paket yoneticileri durdu.")
    return basarili


def kilit_bekle(saniye=30):
    """Kilidin serbest kalmasini bekler. Silme YOK."""
    gunluk("--> Kilidin serbest kalmasi bekleniyor (en fazla %d sn)..." % saniye)
    for i in range(saniye):
        mesgul = [y for y, _ in KILIT_DOSYALARI if kilit_durumu(y) is True]
        if not mesgul:
            gunluk("    Kilit serbest.")
            return True
        time.sleep(1)
    gunluk("    Kilit hala mesgul: %s" % ", ".join(mesgul))
    return False


def onar(gorevler):
    sira = ["surec_durdur", "dpkg_configure", "apt_fix_broken"]
    basarili = True
    for anahtar in [a for a in sira if a in gorevler]:
        if anahtar == "surec_durdur":
            gunluk("--> Paket yoneticileri durduruluyor...")
            basarili &= surecleri_durdur()
        elif anahtar == "dpkg_configure":
            if not kilit_bekle():
                gunluk("    ATLANDI: kilit mesgul oldugu icin dpkg calistirilmadi.")
                basarili = False
                gunluk("")
                continue
            gunluk("--> dpkg --configure -a")
            kod, cikti = komut(["dpkg", "--configure", "-a"])
            gunluk(cikti or "(cikti yok)")
            basarili &= (kod == 0)
        elif anahtar == "apt_fix_broken":
            if not kilit_bekle():
                gunluk("    ATLANDI: kilit mesgul oldugu icin apt calistirilmadi.")
                basarili = False
                gunluk("")
                continue
            gunluk("--> apt-get install -f -y")
            kod, cikti = komut(["apt-get", "install", "-f", "-y"])
            gunluk(cikti or "(cikti yok)")
            basarili &= (kod == 0)
        gunluk("")
    return basarili


def main():
    if os.geteuid() != 0:
        yaz({"tur": "hata", "metin": "Bu betik yonetici yetkisiyle calismalidir."})
        sys.exit(1)

    yaz({"tur": "hazir", "surum": SURUM})

    for satir in sys.stdin:
        satir = satir.strip()
        if not satir:
            continue
        try:
            istek = json.loads(satir)
        except ValueError:
            yaz({"tur": "hata", "metin": "Gecersiz istek."})
            continue

        adi = istek.get("komut")
        if adi == "teshis":
            yaz({"tur": "teshis", "sorunlar": teshis()})
        elif adi == "onar":
            basarili = onar(istek.get("gorevler") or [])
            yaz({"tur": "onarim_bitti", "basarili": bool(basarili)})
        elif adi == "cikis":
            break
        else:
            yaz({"tur": "hata", "metin": "Bilinmeyen komut: %s" % adi})


if __name__ == "__main__":
    main()
