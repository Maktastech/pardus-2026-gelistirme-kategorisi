# Pardus System Health & Journal Log Doctor

> TEKNOFEST Pardus Hata Yakalama ve Öneri Yarışması — **Geliştirme Kategorisi**
> Önem derecesi: **Yüksek**

`journalctl -p <öncelik> -o json` çıktısı bir Regex kural motorundan geçirilir.

---

## Problem

Sistem çöktüğünde veya bir servis başlamadığında cevap `journalctl` kayıtlarındadır; ancak bu kayıtlar İngilizce, teknik ve son kullanıcı için anlamsızdır. Kullanıcı sorunu tarif edemediği için destek de alamaz.

## Çözüm

`journalctl -p <öncelik> -o json` çıktısı bir Regex kural motorundan geçirilir. Her kural bir hata desenini "Bu neden oldu?" ve "Nasıl çözülür?" başlıklı Türkçe açıklamaya eşler. Aynı türden kayıtlar gruplanır, sıklığa göre sıralanır ve rapor olarak dışa aktarılabilir.

## Özellikler

- 10 hazır kural: OOM, disk G/Ç hatası, segfault, servis hatası, disk dolu, GPU, USB, termal vb.
- Önem seviyesi ve zaman aralığı seçimi
- Kayıtların soruna göre gruplanması
- Türkçe neden/çözüm açıklamaları
- Kural listesi tek bir sabitte - kolayca genişletilebilir

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
cd 05-pardus-log-doctor
sudo ./install.sh
```

Kaldırmak için:

```bash
sudo ./uninstall.sh
```

### Kurulmadan denemek

```bash
python3 src/pardus_log_doctor.py
```

## Bağımlılıklar

`python3, python3-pyqt5, systemd`

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
05-pardus-log-doctor/
├── src/pardus_log_doctor.py     # uygulama
├── data/
│   ├── pardus-log-doctor.desktop   # menü girdisi
├── install.sh
├── uninstall.sh
├── LICENSE
└── README.md
```

## Katkı ve Lisans

GPL-3.0 ile lisanslanmıştır. Hata bildirimi ve katkı için "Issues" bölümünü kullanabilirsiniz.
