import csv
import os
import threading
from datetime import datetime

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# ── Sartname 9.2-f/h ─────────────────────────────────────────────────────────
# Izleme merkezi kaydi: ';' ayracli, birimli baslik satiri,
# her oturumda essiz dosya adi (uzerine yazma olmasin).
#
# NOT: Dosya, ilk kayit geldiginde acilir (lazy). Boylece hangi process
# yazarsa yazsin (runserver, telemetri_dinle, daphne) dogru calisir ve
# veri gelmeyen process'ler bos dosya olusturmaz.

KAYIT_KLASORU = "kayitlar"
BASLIK = ['zaman_ms', 'hiz_kmh', 'T_bat_C', 'V_bat_V', 'kalan_enerji_Wh']

_csv_dosyasi = None
_csv_lock = threading.Lock()


def oturum_baslat(zorla: bool = False):
    """Yeni kayit dosyasi olusturur ve yolunu doner.

    zorla=False ise ve dosya zaten varsa mevcut dosya kullanilir.
    """
    global _csv_dosyasi

    with _csv_lock:
        if _csv_dosyasi and not zorla:
            return _csv_dosyasi

        os.makedirs(KAYIT_KLASORU, exist_ok=True)
        ad = os.path.join(
            KAYIT_KLASORU,
            f"telemetri_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        with open(ad, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f, delimiter=';').writerow(BASLIK)

        _csv_dosyasi = ad
        print(f"Kayit dosyasi olusturuldu: {ad}")
        return ad


def aktif_dosya():
    """Aktif CSV dosyasinin yolu (yoksa olusturur)."""
    return _csv_dosyasi or oturum_baslat()


def csv_kaydet(kayit):
    """Sartname 9.2-f: her satirda bir ornekleme, ';' ayracli."""
    dosya = aktif_dosya()
    try:
        with _csv_lock:
            with open(dosya, 'a', newline='', encoding='utf-8') as f:
                csv.writer(f, delimiter=';').writerow([
                    kayit.zaman_ms,
                    kayit.hiz_kmh,
                    kayit.T_bat_C,
                    kayit.V_bat_V,
                    kayit.kalan_enerji,
                ])
    except Exception as e:
        print(f"CSV yazma hatasi: {e}")


def websocket_yayinla(kayit):
    """Dashboard'a canli veri gonder.

    Kanal katmani yoksa veya hata verirse kayit islemi bozulmaz.
    """
    try:
        layer = get_channel_layer()
        if layer is None:
            return
        async_to_sync(layer.group_send)(
            "telemetri",
            {
                "type": "telemetri_mesaj",
                "data": {
                    "zaman_ms":     kayit.zaman_ms,
                    "hiz_kmh":      kayit.hiz_kmh,
                    "T_bat_C":      kayit.T_bat_C,
                    "V_bat_V":      kayit.V_bat_V,
                    "kalan_enerji": kayit.kalan_enerji,
                }
            }
        )
    except Exception as e:
        print(f"WebSocket yayin hatasi: {e}")


def kayit_isle(veri: dict):
    """Gelen telemetri paketini dogrula, kaydet, yayinla.

    Doner: (basarili_mi, hatalar)
    """
    from .serializers import TelemetriSerializer

    s = TelemetriSerializer(data=veri)
    if not s.is_valid():
        return False, s.errors

    kayit = s.save()
    csv_kaydet(kayit)
    websocket_yayinla(kayit)
    return True, None
