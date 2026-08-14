#!/usr/bin/env python3
"""
TULPAR TELEMETRI - Tek tikla baslatici

Bu dosya calistirildiginda:
  1. Django web sunucusunu arka planda baslatir
  2. Ground module'u dinleyip veriyi sunucuya aktarir
  3. Tarayiciyi otomatik acar (dashboard)

Kullanici hicbir terminal komutu yazmaz. Sadece bu dosyayi calistirir:
  Windows : baslat.py dosyasina cift tikla (ya da baslat.bat)
  Mac     : baslat.command dosyasina cift tikla
  Terminal: python baslat.py

Durdurmak icin pencereyi kapat ya da Ctrl+C.
"""

import os
import sys
import time
import threading
import webbrowser

# --- Django ortamini hazirla ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "izleme.settings")

# Bu dosyanin bulundugu klasoru path'e ekle (exe icinden de calissin)
BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

ADRES = "127.0.0.1"
PORT = 8000
URL = f"http://{ADRES}:{PORT}/"


def _migrasyon_yap():
    """Ilk calistirmada veritabani tablolarini olustur."""
    from django.core.management import call_command
    try:
        call_command("migrate", "--noinput", verbosity=0)
    except Exception as e:
        print(f"[UYARI] migrate hatasi: {e}")


def _sunucu_calistir():
    """Django ASGI sunucusunu (WebSocket destekli) baslat."""
    import django
    django.setup()
    _migrasyon_yap()

    # Daphne ASGI sunucusu - WebSocket icin runserver yerine bunu kullaniyoruz
    from daphne.server import Server
    from daphne.endpoints import build_endpoint_description_strings
    from izleme.asgi import application

    endpoints = build_endpoint_description_strings(host=ADRES, port=PORT)
    print(f"[SUNUCU] Baslatiliyor: {URL}")
    Server(
        application=application,
        endpoints=endpoints,
        signal_handlers=False,   # ana thread disinda calistigi icin kapali
        verbosity=0,
    ).run()


def _dinleyici_calistir():
    """Ground module'u dinle. Sunucu ayaga kalkana kadar bekler."""
    import django
    django.setup()

    # Sunucunun hazir olmasini bekle
    time.sleep(4)

    from django.core.management import call_command
    while True:
        try:
            print("[DINLEYICI] Ground module dinleniyor...")
            call_command("lora_dinle")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[DINLEYICI] Hata: {e} - 5 sn sonra tekrar denenecek")
            time.sleep(5)


def _tarayici_ac():
    """Sunucu hazir olunca tarayiciyi ac."""
    time.sleep(5)
    print(f"[TARAYICI] Aciliyor: {URL}")
    try:
        webbrowser.open(URL)
    except Exception as e:
        print(f"[TARAYICI] Otomatik acilamadi: {e}")
        print(f"           Tarayicida su adresi acin: {URL}")


def main():
    print("=" * 55)
    print("  TULPAR TELEMETRI IZLEME MERKEZI")
    print("=" * 55)
    print(f"  Panel adresi : {URL}")
    print(f"  Durdurmak icin : Ctrl+C  ya da pencereyi kapatin")
    print("=" * 55)

    # Dinleyici ve tarayici arka planda (daemon = ana cikinca kapanir)
    threading.Thread(target=_dinleyici_calistir, daemon=True).start()
    threading.Thread(target=_tarayici_ac, daemon=True).start()

    # Sunucu ana thread'de calisir (sinyalleri yakalayabilsin)
    try:
        _sunucu_calistir()
    except KeyboardInterrupt:
        print("\n[KAPANIYOR] Gorusuruz!")


if __name__ == "__main__":
    main()
