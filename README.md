# Pardus Geliştirme ve Bakım Araçları Seti 🚀

Bu depo, **TEKNOFEST 2026 Pardus Hata Yakalama ve Öneri Yarışması (Geliştirme Kategorisi)** kapsamında son kullanıcıların Pardus işletim sistemini daha verimli, güvenli ve performanslı kullanabilmesi amacıyla sıfırdan geliştirilmiş **10 farklı aracı** içermektedir.

Tüm araçlar Pardus'un yerel yapısına uygun (GTK/Qt entegre) ve kullanıcı dostu arayüzlere (GUI) sahip olacak şekilde Python ile kodlanmıştır.

---

## 🛠️ Geliştirilen Araçlar ve Özellikleri

### 1. Pardus Disk Temizleyici (09-pardus-cache-cleaner)
Gereksiz paket önbelleklerini, eski kernel dosyalarını ve yetim paketleri silerek sistemde güvenle yer açar.
![Disk Temizleyici](assets/cache-cleaner.png)

### 2. Pardus Masaüstü Kurtarıcı (08-pardus-desktop-restorer)
XFCE panel ve tema ayarlarını yedekler, bozulma anında tek tıkla geri yükler.
![Masaüstü Kurtarıcı](assets/desktop-restorer.png)

### 3. Pardus Paket Doktoru (03-pardus-apt-doctor)
Yarım kalan kurulumları, dpkg/apt kilitlenmelerini ve bozuk paketleri tek tıkla tespit edip onarır.
![Paket Doktoru](assets/apt-doctor.png)

### 4. Pardus Sistem Günlük Doktoru (05-pardus-log-doctor)
Karmaşık Linux sistem hata mesajlarını (journal) analiz edip Türkçe ve anlaşılır çözüm önerileri sunar.
![Log Doktoru](assets/log-doctor.png)

### 5. Pardus Açılış Analiz Paneli (06-pardus-boot-profiler)
Pardus'un açılışını (boot) yavaşlatan servisleri analiz edip listeler, optimizasyon sağlar.
![Boot Profiler](assets/boot-profiler.png)

### 6. Pardus Çevrimdışı Paket Hazırlayıcı (10-pardus-offline-bundler)
İnterneti olmayan Pardus makinelerine program kurabilmek için paketleri bağımlılıklarıyla beraber indirip arşivler.
![Çevrimdışı Paket Hazırlayıcı](assets/offline-bundler.png)

### 7. Diğer Arkaplan ve İzleme Araçları
- **01-pardus-usb-syncguard (USB Senkronizasyon Koruyucu):** Büyük dosya kopyalamalarında yaşanan veri kayıplarını önler.
- **02-pardus-ram-guard (RAM Koruyucu):** Arkaplanda çalışarak bellek sızıntılarını tespit eder (Tepsi simgesi üzerinden çalışır).
- **04-pardus-port-inspector (Port İnspektörü):** Sistemdeki açık portları ve internet trafiği oluşturan uygulamaları izler.
- **07-pardus-thermal-guard (Termal Koruma):** İşlemci sıcaklığını anlık takip edip donanımı korur.

---

## 💻 Kurulum ve Çalıştırma

Tüm araçlar Pardus 25 XFCE üzerinde başarıyla test edilmiştir.

### Kurulum (Debian Paketi Olarak)
Her araç için ayrı ayrı Debian paketi oluşturulmuştur. Paketleri GitHub Actions (CI) sekmesinden (Artifacts) indirebilirsiniz. 
Geliştirici olarak yerelde derlemek isterseniz kök dizindeki `./build-all-debs.sh` betiğini çalıştırarak tüm `.deb` dosyalarını üretebilir ve `sudo apt install ./dist/*.deb` komutu ile sisteme kurabilirsiniz.

### Kaynak Koddan Çalıştırma
Debian paketi kurmadan test etmek isterseniz, ilgili aracın klasörüne girip `python3 src/dosya_adi.py` şeklinde çalıştırabilirsiniz (Bağımlılıklar: `python3-pyqt5`). Kullanım detayları için araçların içindeki `docs/KULLANIM.md` dosyalarına göz atabilirsiniz.

---

## 🏗️ Mimari Kararlar ve CI Süreci

* **Güvenlik ve Yetki Modeli (pkexec JSON Süreci):** `03-pardus-apt-doctor` gibi yetki gerektiren araçlarda güvenlik için "Ayrıcalık Ayrımı" (Privilege Separation) kullanılmıştır. GUI normal kullanıcı olarak çalışırken, root yetkisi gereken işlemler için `pkexec` ile bir defalık yardımcı (helper) Python süreci başlatılır. GUI ve yardımcı süreç, birbirleriyle `stdin/stdout` üzerinden standart JSON veri formatıyla güvenli bir şekilde haberleşir. Kullanıcıdan her işlemde tekrar tekrar şifre istenmesi engellenmiştir.
* **Saf İş Mantığı ve Pytest Testleri:** Araçların çekirdek kuralları ve veri işleme fonksiyonları (`kurallar.py`, `ayristirma.py` vb.) PyQt5 kütüphanelerinden arındırılarak bağımsız modüller haline getirilmiştir. Bu sayede grafiksel arayüze ihtiyaç duyulmadan mantık doğrulamaları için `.github` üzerinde çalışan otomatize `pytest` birim testleri (unit test) yazılmıştır.
* **Sürekli Entegrasyon (CI/CD):** Projeye dahil edilen `.github/workflows/ci.yml` dosyası sayesinde; her kod gönderiminde otomatik olarak statik kod analizi (`ruff`), birim testleri (`pytest`), paket derlemesi (`dpkg-buildpackage`) yapılır. Derlenen paketlerin bağımlılık listeleri ve kalite denetimi `lintian` ile test edilerek Ubuntu runner'a test kurulumu yapılır.
