# Pardus Thermal Throttling Guard

> TEKNOFEST Pardus Hata Yakalama ve Öneri Yarışması — **Geliştirme Kategorisi**
> Önem derecesi: **Orta / Performans**

`/sys/class/thermal/` ve `cpufreq` verileri okunarak sıcaklık ve anlık/azami frekans oranı gösterilir.

---

## Problem

Düşük donanımlı ve eski cihazlarda işlemci ısındığında frekans düşürülür (thermal throttling); sistem yavaşlar ama kullanıcı bunun nedenini bilemez, donanımın bozulduğunu sanır.

## Çözüm

`/sys/class/thermal/` ve `cpufreq` verileri okunarak sıcaklık ve anlık/azami frekans oranı gösterilir. Intel işlemcilerdeki donanımsal `core_throttle_count` sayacı okunarak gerçekten hız kısıtlaması yaşanıp yaşanmadığı raporlanır. Eşik aşıldığında tepsiden bildirim gönderilir.

## Özellikler

- Tüm termal bölgelerin canlı sıcaklığı
- Çekirdek başına anlık/azami frekans ve governor
- Donanımsal throttling sayacı
- Ayarlanabilir uyarı eşiği ve masaüstü bildirimi
- Sensör bulunmayan sanal makinelerde temiz uyarı

---

## Ekran Görüntüleri

<!-- Uygulamayı Pardus 25'te çalıştırıp aşağıdaki dosyaları ekleyin -->

| Ana ekran | Uyarı durumu |
|---|---|
| ![ana ekran](docs/ekran-1.png) | ![uyari](docs/ekran-2.png) |

---

## Sorun Giderme

```bash
pardus-thermal-guard --tani
```

Termal bölgeleri, çekirdek frekanslarını ve throttling sayacını listeler.

> **Sanal makinede test edilemez.** VirtualBox/VMware misafir sistemlerinde
> `/sys/class/thermal` ve `cpufreq` genelde bulunmaz. Araç bu durumu düzgün
> bildirir ama anlamlı bir ölçüm için fiziksel makine gerekir.

## Kurulum

```bash
git clone <repo-adresi>
cd 07-pardus-thermal-guard
sudo ./install.sh
```

Kaldırmak için:

```bash
sudo ./uninstall.sh
```

### Kurulmadan denemek

```bash
python3 src/pardus_thermal_guard.py
```

## Bağımlılıklar

`python3, python3-pyqt5`

Pardus 25'te `python3-pyqt5` ve `python3-psutil` depolarda mevcuttur.

## Arka Planda Otomatik Çalıştırma

Bu araç sistem tepsisinde sürekli çalışacak şekilde tasarlanmıştır.
Oturum açılışında otomatik başlatmak için:

```bash
systemctl --user enable --now pardus-thermal-guard.service
systemctl --user status pardus-thermal-guard.service
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
07-pardus-thermal-guard/
├── src/pardus_thermal_guard.py     # uygulama
├── data/
│   ├── pardus-thermal-guard.desktop   # menü girdisi
│   └── pardus-thermal-guard.service   # arka plan servisi
├── install.sh
├── uninstall.sh
├── LICENSE
└── README.md
```

## Katkı ve Lisans

GPL-3.0 ile lisanslanmıştır. Hata bildirimi ve katkı için "Issues" bölümünü kullanabilirsiniz.
