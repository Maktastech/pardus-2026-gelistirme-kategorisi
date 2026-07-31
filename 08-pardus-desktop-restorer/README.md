# Pardus Desktop Quick Restorer / Session Guard

> TEKNOFEST Pardus Hata Yakalama ve Öneri Yarışması — **Geliştirme Kategorisi**
> Önem derecesi: **Orta / Kullanılabilirlik**

XFCE için `~/.

---

## Problem

XFCE paneli çöktüğünde veya masaüstü simgeleri kaybolduğunda kullanıcı oturumu kullanılamaz hâle gelir. Çözüm genelde "ayarları sıfırlamak" olur ve tüm özelleştirmeler kaybedilir.

## Çözüm

XFCE için `~/.config/xfce4`, GNOME için ilgili `dconf` ağaçları zaman damgalı `.tar.gz` yedeklerine alınır. Sorun çıktığında istenen yedek geri yüklenir ve panel yeniden başlatılır. Son çare olarak varsayılana sıfırlama seçeneği de vardır.

## Özellikler

- XFCE ve GNOME desteği, ortam otomatik algılanır
- Zaman damgalı yedek arşivleri
- Tek tıkla geri yükleme ve panel yeniden başlatma
- Varsayılana sıfırlama (onaylı)
- Yönetici yetkisi gerektirmez - tamamen kullanıcı dizininde çalışır

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
cd 08-pardus-desktop-restorer
sudo ./install.sh
```

Kaldırmak için:

```bash
sudo ./uninstall.sh
```

### Kurulmadan denemek

```bash
python3 src/pardus_desktop_restorer.py
```

## Bağımlılıklar

`python3, python3-pyqt5, xfconf | dconf-cli`

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
08-pardus-desktop-restorer/
├── src/pardus_desktop_restorer.py     # uygulama
├── data/
│   ├── pardus-desktop-restorer.desktop   # menü girdisi
├── install.sh
├── uninstall.sh
├── LICENSE
└── README.md
```

## Katkı ve Lisans

GPL-3.0 ile lisanslanmıştır. Hata bildirimi ve katkı için "Issues" bölümünü kullanabilirsiniz.
