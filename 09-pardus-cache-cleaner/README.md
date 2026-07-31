# Pardus Local Repository & Cache Cleaner

> TEKNOFEST Pardus Hata Yakalama ve Öneri Yarışması — **Geliştirme Kategorisi**
> Önem derecesi: **Orta / Performans**

Altı temizlik alanı taranır ve her biri için kazanılacak alan tahmini gösterilir.

---

## Problem

`/var/cache/apt/archives` içindeki indirilmiş paketler, artık kullanılmayan bağımlılıklar ve eski çekirdek sürümleri zamanla gigabaytlarca yer kaplar. Özellikle küçük `/boot` bölümü dolduğunda güncellemeler tamamen durur.

## Çözüm

Altı temizlik alanı taranır ve her biri için kazanılacak alan tahmini gösterilir. Her maddede ne yapıldığı ve riskin ne olduğu Türkçe açıklanır. Çalışan çekirdek ve bir önceki sürüm daima korunur; kaldırma işlemleri `apt-get` üzerinden yapıldığı için bağımlılıklar bozulmaz.

## Özellikler

- apt önbelleği, yetim paketler, eski çekirdekler, journal, çöp kutusu, ~/.cache
- Her madde için tahmini kazanç ve risk açıklaması
- Çalışan çekirdek koruması
- Yalnızca `apt-get` üzerinden kaldırma - manuel dosya silme yok
- Kök bölümdeki boş alanın canlı gösterimi

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
cd 09-pardus-cache-cleaner
sudo ./install.sh
```

Kaldırmak için:

```bash
sudo ./uninstall.sh
```

### Kurulmadan denemek

```bash
python3 src/pardus_cache_cleaner.py
```

## Bağımlılıklar

`python3, python3-pyqt5, policykit-1`

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
09-pardus-cache-cleaner/
├── src/pardus_cache_cleaner.py     # uygulama
├── data/
│   ├── pardus-cache-cleaner.desktop   # menü girdisi
├── install.sh
├── uninstall.sh
├── LICENSE
└── README.md
```

## Katkı ve Lisans

GPL-3.0 ile lisanslanmıştır. Hata bildirimi ve katkı için "Issues" bölümünü kullanabilirsiniz.
