import re

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

def kayit_yorumla(mesaj):
    for desen, baslik, neden, cozum in KURALLAR:
        if re.search(desen, mesaj, re.IGNORECASE):
            return baslik, neden, cozum
    return None
