# Pardus Offline Package & Dependency Bundler

> TEKNOFEST Pardus Hata Yakalama ve Öneri Yarışması — **Geliştirme Kategorisi**
> Önem derecesi: **Orta / Kullanılabilirlik**

`apt-get install --print-uris` ile paketin tüm bağımlılık ağacı çözülür, `.

---

## Problem

Kamu kurumlarında ve okul laboratuvarlarında internete kapalı Pardus makineleri yaygındır. Bu makinelere bir uygulama kurmak için tüm bağımlılık ağacının elle indirilmesi gerekir; bu da pratikte imkânsızdır.

## Çözüm

`apt-get install --print-uris` ile paketin tüm bağımlılık ağacı çözülür, `.deb` dosyaları indirilir ve içine hazır bir `kur.sh` betiği konularak `.tar.gz` arşivi oluşturulur. İnternetsiz makinede arşiv açılıp `sudo ./kur.sh` çalıştırılması yeterlidir. Hem GUI hem komut satırı desteklenir.

## Özellikler

- Tam bağımlılık ağacı çözümü
- Kendi kurulum betiğini içeren taşınabilir arşiv
- Arşiv içinde paket listesi ve mimari bilgisi (BILGI.txt)
- Grafik arayüz + `pardus-offline-bundler <paket>` komut satırı kullanımı
- USB ile taşınabilir, tek komutla kurulum

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
cd 10-pardus-offline-bundler
sudo ./install.sh
```

Kaldırmak için:

```bash
sudo ./uninstall.sh
```

### Kurulmadan denemek

```bash
python3 src/pardus_offline_bundler.py
```

## Bağımlılıklar

`python3, python3-pyqt5, wget, apt`

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
10-pardus-offline-bundler/
├── src/pardus_offline_bundler.py     # uygulama
├── data/
│   ├── pardus-offline-bundler.desktop   # menü girdisi
├── install.sh
├── uninstall.sh
├── LICENSE
└── README.md
```

## Katkı ve Lisans

GPL-3.0 ile lisanslanmıştır. Hata bildirimi ve katkı için "Issues" bölümünü kullanabilirsiniz.
