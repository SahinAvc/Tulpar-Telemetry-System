# Tulpar Telemetri İzleme Sistemi

Elektrikli araç için tasarlanmış, gerçek zamanlı telemetri izleme merkezi.
Araçtan (Raspberry Pi) 433 MHz radyo ile gönderilen verileri alır, kaydeder
ve web tabanlı bir panoda canlı gösterir.

## Özellikler

- **Canlı telemetri paneli** — hız, batarya sıcaklığı, gerilim ve kalan enerji
  WebSocket üzerinden anlık güncellenir.
- **Veri bütünlüğü** — her paket CRC16 ile doğrulanır, bozuk paketler reddedilir.
- **Otomatik kayıt** — gelen tüm veriler `;` ayraçlı CSV dosyasına yazılır
  (her oturumda eşsiz dosya adı).
- **Bağlantı kesintisi takibi** — 60 saniyeyi aşan kesintiler izlenir ve raporlanır.
- **Masaüstü uygulaması** — tarayıcı gerektirmeden kendi penceresinde açılır
  (PyInstaller ile `.exe` / `.app` olarak paketlenebilir).

## Sistem Mimarisi

```
Araç (Raspberry Pi) → 433 MHz radyo → Ground Module (USB) → Bu uygulama
                                                                  ↓
                                              Veritabanı + CSV + canlı pano
```

## Kurulum

1. Gereksinimleri kurun:

   ```
   python -m venv venv
   venv\Scripts\activate          # Windows
   source venv/bin/activate       # Mac / Linux
   pip install -r requirements.txt
   ```

2. Veritabanını hazırlayın:

   ```
   python manage.py migrate
   ```

3. Uygulamayı başlatın (kendi penceresinde açılır):

   ```
   python app.py
   ```

   Ya da sunucu + dinleyiciyi ayrı çalıştırmak için:

   ```
   python manage.py runserver      # 1. terminal
   python manage.py lora_dinle      # 2. terminal
   ```

## Uygulama Olarak Derleme (.exe / .app)

Çift tıklanabilir uygulama üretmek için `DERLEME_REHBERI.txt` dosyasına bakın.
Kısaca:

```
pip install pyinstaller
pyinstaller TulparTelemetri.spec
```

Windows'ta `dist/TulparTelemetri.exe`, Mac'te `dist/TulparTelemetri.app` oluşur.
Not: Windows uygulaması Windows'ta, Mac uygulaması Mac'te derlenmelidir.

## Ground Module Bağlantısı

Uygulama, telemetri radyosunun (RFD SiK / HM-TRP 433 MHz) takılı olduğu
COM portunu otomatik bulur. Bulamazsa `--port` ile elle belirtilebilir:

```
python manage.py lora_dinle --port COM5
```

## Lisans

Bu proje ekip içi kullanım içindir. Tüm hakları saklıdır.
