#!/usr/bin/env python3
"""
TULPAR TELEMETRI - Masaustu Uygulamasi

Django + Daphne sunucusunu arka planda calistirir ve dashboard'u
uygulamanin KENDI PENCERESINDE gosterir (tarayici acilmaz).

Gelistirme sirasinda dogrudan calistirilabilir:
    pip install pywebview daphne
    python app.py

Dagitim icin PyInstaller ile .exe / .app'e paketlenir (bkz. derle.py).
"""

import os
import sys
import time
import socket
import threading

import webview   # pip install pywebview

# ── Yol ayari (PyInstaller ile paketlenince de calissin) ─────────────────────
if getattr(sys, "frozen", False):
    # PyInstaller ile paketlenmis: kaynaklar _MEIPASS altinda
    BASE = sys._MEIPASS
else:
    BASE = os.path.dirname(os.path.abspath(__file__))

if BASE not in sys.path:
    sys.path.insert(0, BASE)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "izleme.settings")

ADRES = "127.0.0.1"
PORT = 8000
URL = f"http://{ADRES}:{PORT}/"

_sunucu_hazir = threading.Event()


def _port_acik_mi(host, port):
    """Sunucu gercekten dinlemeye basladi mi kontrol et."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def _sunucu_calistir():
    """Django ASGI (Daphne) sunucusunu baslat."""
    import django
    django.setup()

    from django.core.management import call_command
    try:
        call_command("migrate", "--noinput", verbosity=0)
    except Exception as e:
        print(f"[UYARI] migrate: {e}")

    from daphne.server import Server
    from daphne.endpoints import build_endpoint_description_strings
    from izleme.asgi import application

    endpoints = build_endpoint_description_strings(host=ADRES, port=PORT)
    print(f"[SUNUCU] {URL}")
    Server(
        application=application,
        endpoints=endpoints,
        signal_handlers=False,
        verbosity=0,
    ).run()


def _dinleyici_calistir():
    """Ground module'u dinle. Sunucu hazir olana kadar bekler."""
    _sunucu_hazir.wait(timeout=30)
    import django
    django.setup()
    from django.core.management import call_command
    while True:
        try:
            print("[DINLEYICI] Ground module dinleniyor...")
            call_command("lora_dinle")
        except Exception as e:
            print(f"[DINLEYICI] {e} - 5 sn sonra tekrar")
            time.sleep(5)


def _sunucuyu_bekle():
    """Sunucu port'u acilana kadar bekle, sonra event'i tetikle."""
    for _ in range(60):          # en fazla 30 sn bekle
        if _port_acik_mi(ADRES, PORT):
            _sunucu_hazir.set()
            return
        time.sleep(0.5)
    print("[UYARI] Sunucu zamaninda ayaga kalkmadi")


def main():
    # Sunucu + dinleyici arka planda
    threading.Thread(target=_sunucu_calistir, daemon=True).start()
    threading.Thread(target=_sunucuyu_bekle, daemon=True).start()
    threading.Thread(target=_dinleyici_calistir, daemon=True).start()

    # Sunucu hazir olana kadar bekle (pencere bos acilmasin)
    _sunucu_hazir.wait(timeout=30)

    # Uygulama penceresi - dashboard burada acilir, tarayici YOK
    webview.create_window(
        "Tulpar Telemetri İzleme Merkezi",
        URL,
        width=1400,
        height=900,
        min_size=(1000, 700),
        background_color="#0a0e17",
    )
    webview.start()   # pencere kapaninca program biter


if __name__ == "__main__":
    main()
