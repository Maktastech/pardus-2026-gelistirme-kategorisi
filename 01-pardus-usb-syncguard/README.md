# Pardus USB Sync-Guard & Buffer Tracker

> TEKNOFEST Pardus Hata Yakalama ve Öneri Yarışması — **Geliştirme Kategorisi**
> Önem derecesi: **Kritik**

Sistem tepsisinde çalışan bir izleyici `Dirty + Writeback` değerlerini yarım saniyede bir okur.

---

## Problem

Pardus'ta USB belleğe büyük bir dosya kopyalandığında dosya yöneticisi ilerleme çubuğu dolduğunda "tamamlandı" görünümü verir; ancak veri hâlâ çekirdeğin yazma tamponundadır (`/proc/meminfo` -> `Dirty`). Kullanıcı bu anda belleği çıkarırsa dosya bozulur, dosya sistemi zarar görebilir. Son kullanıcı için tamponun boşalıp boşalmadığını gösteren hiçbir görsel gösterge yoktur.

## Çözüm

Sistem tepsisinde çalışan bir izleyici `Dirty + Writeback` değerlerini yarım saniyede bir okur. Yazma sürüyorsa simge değişir ve "USB'yi çıkarmayın" bildirimi verilir; tampon boşaldığında "Güvenle çıkarabilirsiniz" bildirimi gönderilir. Pencereden `sync` çalıştırılabilir ve aygıt `udisksctl` ile güvenle çıkarılabilir.

## Özellikler

- Gerçek zamanlı yazma tamponu izleme (`/proc/meminfo`)
- Çıkarılabilir aygıtların otomatik tespiti (`/sys/block/*/removable`)
- Yazma bitince masaüstü bildirimi
- Tek tıkla `sync` + `udisksctl unmount` + `power-off`
- Türkçe arayüz, sistem tepsisinde arka planda çalışır

---

## Ekran Görüntüleri

<!-- Uygulamayı Pardus 25'te çalıştırıp aşağıdaki dosyaları ekleyin -->

| Ana ekran | Uyarı durumu |
|---|---|
| ![ana ekran](docs/ekran-1.png) | ![uyari](docs/ekran-2.png) |

---

## Sorun Giderme

Tepsi simgesi görünmüyorsa veya uygulama çalışmıyor gibi duruyorsa:

```bash
pardus-usb-syncguard --tani
```

Bu komut Qt sürümünü, sistem tepsisinin varlığını, ikonun geçerli olup
olmadığını, tampon değerini ve bağlı tüm blok aygıtlarını (atlananların
gerekçesiyle birlikte) raporlar.

> v2.0 notu: İkonlar `QPainter` ile kodda çizilir, tema ikonuna bağlı değildir.
> Pardus 25'in "Bilge" ikon setinde bir isim bulunmazsa `QIcon.fromTheme` boş
> ikon döndürür ve tepsi simgesi hiç görünmez; bu sorun bu şekilde giderildi.
> Sistem tepsisi hiç yoksa uygulama pencere modunda çalışmaya devam eder.

## Kurulum

```bash
git clone <repo-adresi>
cd 01-pardus-usb-syncguard
sudo ./install.sh
```

Kaldırmak için:

```bash
sudo ./uninstall.sh
```

### Kurulmadan denemek

```bash
python3 src/pardus_usb_syncguard.py
```

## Bağımlılıklar

`python3, python3-pyqt5, udisks2`

Pardus 25'te `python3-pyqt5` ve `python3-psutil` depolarda mevcuttur.

## Arka Planda Otomatik Çalıştırma

Bu araç sistem tepsisinde sürekli çalışacak şekilde tasarlanmıştır.
Oturum açılışında otomatik başlatmak için:

```bash
systemctl --user enable --now pardus-usb-syncguard.service
systemctl --user status pardus-usb-syncguard.service
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
01-pardus-usb-syncguard/
├── src/pardus_usb_syncguard.py     # uygulama
├── data/
│   ├── pardus-usb-syncguard.desktop   # menü girdisi
│   └── pardus-usb-syncguard.service   # arka plan servisi
├── install.sh
├── uninstall.sh
├── LICENSE
└── README.md
```

## Katkı ve Lisans

GPL-3.0 ile lisanslanmıştır. Hata bildirimi ve katkı için "Issues" bölümünü kullanabilirsiniz.
