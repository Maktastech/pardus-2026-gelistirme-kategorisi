# Pardus Rogue Socket & Port Inspector

> TEKNOFEST Pardus Hata Yakalama ve Öneri Yarışması — **Geliştirme Kategorisi**
> Önem derecesi: **Yüksek / Güvenlik**

`psutil.

---

## Problem

Masaüstü kullanıcısı, makinesinde hangi servislerin dışarıya port açtığını göremez. `ss -tulpn` çıktısını okumak son kullanıcı için mümkün değildir. Bu da beklenmedik şekilde dış ağa açık kalmış servislerin fark edilmemesine yol açar.

## Çözüm

`psutil.net_connections()` ile tüm TCP/UDP soketleri, bağlı süreç, kullanıcı ve çalıştırılabilir dosya yolu ile birlikte listelenir. Basit bir risk motoru her satırı değerlendirir: dış ağa açık dinleyen tanımsız servisler ve `/tmp` gibi dizinlerden çalışan ağ süreçleri şüpheli olarak işaretlenir. Şüpheli port `ufw` ile tek tıkla kapatılabilir.

## Özellikler

- Dinleyen ve kurulu tüm bağlantıların süreç eşlemeli listesi
- Renk kodlu risk değerlendirmesi (normal / dikkat / şüpheli)
- Bilinen servis portları için Türkçe açıklama
- `ufw deny` entegrasyonu ve güvenlik duvarı durumu
- Metin rapor dışa aktarma

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
cd 04-pardus-port-inspector
sudo ./install.sh
```

Kaldırmak için:

```bash
sudo ./uninstall.sh
```

### Kurulmadan denemek

```bash
python3 src/pardus_port_inspector.py
```

## Bağımlılıklar

`python3, python3-pyqt5, python3-psutil, ufw`

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
04-pardus-port-inspector/
├── src/pardus_port_inspector.py     # uygulama
├── data/
│   ├── pardus-port-inspector.desktop   # menü girdisi
├── install.sh
├── uninstall.sh
├── LICENSE
└── README.md
```

## Katkı ve Lisans

GPL-3.0 ile lisanslanmıştır. Hata bildirimi ve katkı için "Issues" bölümünü kullanabilirsiniz.
