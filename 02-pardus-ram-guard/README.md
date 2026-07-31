# Pardus Dynamic RAM & OOM Crash Preventer

> TEKNOFEST Pardus Hata Yakalama ve Öneri Yarışması — **Geliştirme Kategorisi**
> Önem derecesi: **Kritik**

RAM ve swap doluluğu sürekli izlenir.

---

## Problem

Düşük bellekli makinelerde ve sanal makinelerde RAM dolduğunda sistem yanıt vermez hâle gelir; çekirdeğin OOM-killer'ı devreye girene kadar masaüstü tamamen kilitlenir ve kullanıcı hangi uygulamanın belleği tükettiğini göremez. Pardus'ta bu ana müdahale eden grafiksel bir araç bulunmuyor.

## Çözüm

RAM ve swap doluluğu sürekli izlenir. Kullanıcının belirlediği kritik eşiğe (varsayılan %93) ulaşıldığında masaüstü bildirimi gönderilir ve pencere öne getirilir. En çok bellek tüketen 10 süreç listelenir; kullanıcı süreci dondurabilir (`SIGSTOP`), devam ettirebilir (`SIGCONT`) veya güvenle kapatabilir (`SIGTERM`). Kritik sistem süreçleri beyaz listeyle korunur.

## Özellikler

- RAM/Swap doluluğunun canlı takibi
- Ayarlanabilir kritik eşik
- En çok bellek tüketen süreçlerin sıralanması
- SIGSTOP ile dondurma - sistemi kilitlemeden zaman kazandırır
- systemd, Xorg, gnome-shell gibi kritik süreçler korunur

---

## Ekran Görüntüleri

<!-- Uygulamayı Pardus 25'te çalıştırıp aşağıdaki dosyaları ekleyin -->

| Ana ekran | Uyarı durumu |
|---|---|
| ![ana ekran](docs/ekran-1.png) | ![uyari](docs/ekran-2.png) |

---

## Sorun Giderme

```bash
pardus-ram-guard --tani
```

Sistem tepsisi durumu, ikon geçerliliği, anlık RAM/Swap değerleri ve en çok
bellek tüketen 3 süreci raporlar. Tepsi simgesi tema ikonuna bağlı değildir;
tepsi hiç yoksa uygulama pencere modunda çalışır.

## Kurulum

```bash
git clone <repo-adresi>
cd 02-pardus-ram-guard
sudo ./install.sh
```

Kaldırmak için:

```bash
sudo ./uninstall.sh
```

### Kurulmadan denemek

```bash
python3 src/pardus_ram_guard.py
```

## Bağımlılıklar

`python3, python3-pyqt5, python3-psutil`

Pardus 25'te `python3-pyqt5` ve `python3-psutil` depolarda mevcuttur.

## Arka Planda Otomatik Çalıştırma

Bu araç sistem tepsisinde sürekli çalışacak şekilde tasarlanmıştır.
Oturum açılışında otomatik başlatmak için:

```bash
systemctl --user enable --now pardus-ram-guard.service
systemctl --user status pardus-ram-guard.service
```


## Test Edildiği Ortam

- **Pardus 25 "BİLGE"** (25.0 / 25.1 / 25.2) — XFCE 4.20 ve GNOME
- Debian 13 tabanı, Linux Kernel 6.12
- Python 3.13, PyQt5 5.15

> Pardus 25, Debian 13 tabanlı olduğu için `policykit-1` paketi artık yok;
> yetki yükseltme `polkitd` + `pkexec` ile yapılır. Kurulum betiği bunu
> otomatik olarak halleder.

## Dizin Yapısı

```
02-pardus-ram-guard/
├── src/pardus_ram_guard.py     # uygulama
├── data/
│   ├── pardus-ram-guard.desktop   # menü girdisi
│   └── pardus-ram-guard.service   # arka plan servisi
├── install.sh
├── uninstall.sh
├── LICENSE
└── README.md
```

## Katkı ve Lisans

GPL-3.0 ile lisanslanmıştır. Hata bildirimi ve katkı için "Issues" bölümünü kullanabilirsiniz.
