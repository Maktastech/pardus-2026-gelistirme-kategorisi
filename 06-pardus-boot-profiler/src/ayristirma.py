import re
import subprocess
import logging

# Kapatilmasi sisteme zarar verebilecek birimler
KORUNAN = {
    "systemd-journald.service", "systemd-logind.service", "dbus.service",
    "systemd-udevd.service", "NetworkManager.service", "polkit.service",
    "gdm.service", "lightdm.service", "systemd-resolved.service",
    "user@1000.service", "systemd-timesyncd.service",
}

# Cogu masaustu kullanicisinda gereksiz olabilen bilinen servisler
GEREKSIZ_OLABILIR = {
    "ModemManager.service": "Mobil modem yoksa gerek yok",
    "bluetooth.service": "Bluetooth kullanmiyorsaniz kapatilabilir",
    "cups.service": "Yazici kullanmiyorsaniz kapatilabilir",
    "cups-browsed.service": "Ag yazicisi aramasi; genelde gereksiz",
    "avahi-daemon.service": "Yerel ag kesfi; kurumsal agda gereksiz olabilir",
    "apt-daily.service": "Arka plan paket kontrolu; ertelenebilir",
    "apt-daily-upgrade.service": "Arka plan yukseltme kontrolu",
    "snapd.service": "Snap paketi kullanmiyorsaniz gereksiz",
}


def sureyi_saniyeye_cevir(metin):
    toplam = 0.0
    for deger, birim in re.findall(r"([\d.]+)(min|ms|s|h)", metin):
        deger = float(deger)
        toplam += {"h": deger * 3600, "min": deger * 60,
                   "s": deger, "ms": deger / 1000.0}[birim]
    return toplam


def acilis_ozeti():
    try:
        s = subprocess.run(["systemd-analyze"], capture_output=True,
                           text=True, timeout=30)
        return s.stdout.strip() or s.stderr.strip()
    except Exception as h:
        return "systemd-analyze calistirilamadi: %s" % h


def blame_listesi():
    try:
        s = subprocess.run(["systemd-analyze", "blame", "--no-pager"],
                           capture_output=True, text=True, timeout=60)
    except subprocess.SubprocessError as e:
        logging.error("blame_listesi subprocess hatasi: %s", e)
        return []
    except OSError as e:
        logging.error("blame_listesi calistirma hatasi: %s", e)
        return []
    satirlar = []
    for satir in s.stdout.splitlines():
        satir = satir.strip()
        if not satir:
            continue
        parcalar = satir.rsplit(" ", 1)
        if len(parcalar) != 2:
            continue
        sure_metni, birim = parcalar[0].strip(), parcalar[1].strip()
        satirlar.append({
            "birim": birim,
            "sure_metni": sure_metni,
            "saniye": sureyi_saniyeye_cevir(sure_metni),
        })
    return satirlar


def birim_durumu(birim):
    try:
        s = subprocess.run(["systemctl", "is-enabled", birim],
                           capture_output=True, text=True, timeout=10)
        return s.stdout.strip() or "bilinmiyor"
    except subprocess.SubprocessError as e:
        logging.error("birim_durumu subprocess hatasi: %s", e)
        return "bilinmiyor"
    except OSError as e:
        logging.error("birim_durumu calistirma hatasi: %s", e)
        return "bilinmiyor"
