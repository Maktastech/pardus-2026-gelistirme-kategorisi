# Pardus App Startup & Boot Profiler

> TEKNOFEST Pardus Hata Yakalama ve Öneri Yarışması — **Geliştirme Kategorisi**
> Önem derecesi: **Orta / Kullanılabilirlik**

`systemd-analyze` özeti ve `blame` çıktısı tabloya dökülür; her servisin toplam açılış süresindeki payı yüzde olarak gösterilir.

---

## Problem

Pardus'un açılış süresini uzatan systemd servislerini görmek için `systemd-analyze blame` komutunu bilmek gerekir. Son kullanıcı hangi servisin gereksiz olduğunu ve kapatmanın güvenli olup olmadığını bilemez.

## Çözüm

`systemd-analyze` özeti ve `blame` çıktısı tabloya dökülür; her servisin toplam açılış süresindeki payı yüzde olarak gösterilir. Bilinen gereksiz servisler için Türkçe öneri sunulur, kritik sistem birimleri kilitlenerek kapatılması engellenir. Değişiklik öncesi etkin servis listesi yedeklenebilir.

## Özellikler

- Servis başına açılış süresi ve yüzde pay
- Renk kodu: kritik / gereksiz olabilir / yavaş
- Tek tıkla `systemctl disable` ve geri alma
- Kritik birimler için koruma listesi
- Geri dönüş için etkin servis listesi yedeği

---

## Ekran Görüntüleri

<!-- Uygulamayı Pardus 25'te çalıştırıp aşağıdaki dosyaları ekleyin -->

| Ana ekran | Uyarı durumu |
|---|---|
| ![ana ekran](docs/ekran-1.png) | ![uyari](docs/ekran-2.png) |

---

## Kurulum

```bash
git clone <repo-adresi>
cd 06-pardus-boot-profiler
sudo ./install.sh
```

Kaldırmak için:

```bash
sudo ./uninstall.sh
```

### Kurulmadan denemek

```bash
python3 src/pardus_boot_profiler.py
```

## Bağımlılıklar

`python3, python3-pyqt5, systemd, policykit-1`

Pardus 25'te `python3-pyqt5` ve `python3-psutil` depolarda mevcuttur.



## Test Edildiği Ortam

- **Pardus 25 "BİLGE"** (25.0 / 25.1 / 25.2) — XFCE 4.20 ve GNOME
- Debian 13 tabanı, Linux Kernel 6.12
- Python 3.13, PyQt5 5.15

> Pardus 25, Debian 13 tabanlı olduğu için `policykit-1` paketi artık yok;
> yetki yükseltme `polkitd` + `pkexec` ile yapılır. Kurulum betiği bunu
> otomatik olarak halleder.

## Dizin Yapısı

```
06-pardus-boot-profiler/
├── src/pardus_boot_profiler.py     # uygulama
├── data/
│   ├── pardus-boot-profiler.desktop   # menü girdisi
├── install.sh
├── uninstall.sh
├── LICENSE
└── README.md
```

## Katkı ve Lisans

GPL-3.0 ile lisanslanmıştır. Hata bildirimi ve katkı için "Issues" bölümünü kullanabilirsiniz.
