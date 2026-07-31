# Pardus Auto-Fixer & Lock Rescue Tool

> TEKNOFEST Pardus Hata Yakalama ve Öneri Yarışması — **Geliştirme Kategorisi**
> Önem derecesi: **Yüksek**

Araç sistemi tarar: çalışan paket yöneticilerini, sahipsiz kilit dosyalarını (`fuser` ile doğrulanır), `dpkg --audit` çıktısını ve `apt-get check` sonucunu değerlendirir.

---

## Problem

`Could not get lock /var/lib/dpkg/lock-frontend` hatası Pardus'a yeni geçen kullanıcıların en sık karşılaştığı sorunlardan biridir. Yarım kalmış kurulumlar ve kırık bağımlılıklar da paket sistemini kullanılamaz hâle getirir. Çözüm için kullanıcıdan terminal komutları bilmesi beklenir.

## Çözüm

Araç sistemi tarar: çalışan paket yöneticilerini, sahipsiz kilit dosyalarını (`fuser` ile doğrulanır), `dpkg --audit` çıktısını ve `apt-get check` sonucunu değerlendirir. Bulunan her sorun Türkçe açıklamasıyla listelenir; kullanıcı seçtiklerini tek tıkla onarır. Yetki yükseltme `pkexec` ile yapılır.

## Yetki Modeli (v1.1)

Uygulama açılışında **bir kez** `pkexec` ile bir yönetici yardımcısı (`pardus-apt-doctor-helper`)
başlatır. Arayüz bu süreçle stdin/stdout üzerinden JSON satırlarıyla konuşur; teşhis ve onarım
dahil sonraki hiçbir işlemde tekrar şifre sorulmaz. Şifre penceresindeki metin, kurulan
polkit kuralı sayesinde Türkçedir ve `rm -f /var/lib/dpkg/lock` gibi ham komut satırı yerine
uygulamanın ne yapmak istediğini açıklar.

Teşhis de root tarafında çalıştığı için kilit dosyalarını tutan **root'a ait süreçler doğru
tespit edilir**. Önceki sürümde `fuser` normal kullanıcı olarak çalıştığından `packagekitd`
gibi süreçler görünmüyor ve kilitler yanlışlıkla "sahipsiz" sayılabiliyordu.

## Güvenlik Kuralları

**Bu araç kilit dosyası silmez.** `/var/lib/dpkg/lock`, `lock-frontend` ve apt kilitleri
her Pardus kurulumunda diskte **zaten vardır**; varlıkları bir hata değildir. Önemli olan
dosyanın `fcntl` (POSIX kayıt kilidi, `F_SETLK`) ile gerçekten tutulup tutulmadığıdır —
apt ve dpkg tam olarak bu mekanizmayı kullanır.

Araç kilidi test etmek için kilidi bir anlık alıp hemen bırakır; sisteme müdahale etmez:

```python
fd = os.open(yol, os.O_RDWR)
fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)   # alınabiliyorsa serbest
fcntl.lockf(fd, fcntl.LOCK_UN)                   # anında bırak
```

Kilit meşgulse yapılan iş: `/proc/<pid>/fd` taranarak kilidi tutan süreç bulunur,
kullanıcıya gösterilir ve durdurulması **önerilir** — silme seçeneği hiç sunulmaz.

Asıl onarım yalnızca standart araçlarla yapılır:

| Sorun | Uygulanan komut |
|---|---|
| Yarım kalmış kurulum | `dpkg --configure -a` |
| Kırık bağımlılık | `apt-get install -f` |
| Kilidi tutan servis | `systemctl stop packagekit` |

Ek kurallar:

- Her onarım komutundan önce kilidin serbest kalması beklenir (en fazla 30 sn); meşguller komut çalıştırılmaz
- `packagekitd` ve `unattended-upgrades` `kill` ile değil `systemctl stop` ile durdurulur
- PackageKit'in arka planda çalışması **normal** kabul edilir, varsayılan olarak işaretlenmez
- "Bilgi" ve "Sorun" seviyeleri ayrıdır; yalnızca gerçek sorunlar varsayılan işaretli gelir
- `dpkg`/`apt-get` bulunamazsa bu bir paket sorunu değil ortam sorunu olarak raporlanır

## Özellikler

- Kilit dosyasının gerçekten sahipsiz olduğunu doğrular (kör silme yapmaz)
- `dpkg --configure -a` ile yarım kalan kurulumları tamamlar
- `apt-get install -f` ile kırık bağımlılıkları onarır
- Her sorun için Türkçe neden/çözüm açıklaması
- Tüm işlemler kullanıcı onayıyla ve pkexec ile

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
cd 03-pardus-apt-doctor
sudo ./install.sh
```

Kaldırmak için:

```bash
sudo ./uninstall.sh
```

### Kurulmadan denemek

```bash
python3 src/pardus_apt_doctor.py
```

## Bağımlılıklar

`python3, python3-pyqt5, polkitd, pkexec`

> Not: Pardus 25 (Debian 13) tabanında `policykit-1` paketi kaldırıldı, yerine `polkitd` ve `pkexec` geldi. `psmisc`/`fuser` bağımlılığı da kalktı; kilit sahipliği `/proc/<pid>/fd` taranarak bulunuyor.

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
03-pardus-apt-doctor/
├── src/pardus_apt_doctor.py   # arayuz (normal kullanici)
├── src/apt_doctor_helper.py   # yonetici yardimcisi (root)
├── data/
│   ├── pardus-apt-doctor.desktop   # menü girdisi
│   └── tr.org.pardus.aptdoctor.policy  # polkit kuralı
├── install.sh
├── uninstall.sh
├── LICENSE
└── README.md
```

## Katkı ve Lisans

GPL-3.0 ile lisanslanmıştır. Hata bildirimi ve katkı için "Issues" bölümünü kullanabilirsiniz.
