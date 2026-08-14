"""
Ground Module (PC) -> Django koprusu (HTTP surumu).

Seri porttan gelen telemetri paketlerini okur, CRC16 ile dogrular ve
Django'nun /api/telemetri/ ucuna POST eder. Kayit isleme (DB + CSV +
WebSocket yayini) runserver process'i icinde yapilir; bu sayede
InMemoryChannelLayer yeterlidir, Redis'e gerek yoktur.

Paket formati (arac tarafi lora5.py ile ayni):
    {"T_bat_C":24.4,"V_bat_V":48.2,"hiz_kmh":30.5,...}*E4D9
    govde JSON + '*' + CRC16/MODBUS (4 haneli hex)

Yeri:  telemetri/management/commands/lora_dinle.py

Calistirma (runserver ayri terminalde acik olmali):
    python manage.py lora_dinle
    python manage.py lora_dinle --port COM5 --baud 115200
    python manage.py lora_dinle --crc-yoksay          (CRC'siz paketleri de kabul et)
    python manage.py lora_dinle --url http://192.168.1.50:8000/api/telemetri/
"""

import json
import time

import requests
import serial
import serial.tools.list_ports
from django.core.management.base import BaseCommand

VARSAYILAN_BAUD = 115200
VARSAYILAN_URL = "http://127.0.0.1:8000/api/telemetri/"

# Sartname 9.2-d: 60 sn'yi asan kesinti stabil calisma sayilmaz
KESINTI_UYARI_S = 60


def crc16(veri: bytes) -> int:
    """CRC-16/MODBUS - arac tarafiyla ayni algoritma."""
    crc = 0xFFFF
    for b in veri:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def paket_coz(satir: str, crc_zorunlu: bool = True):
    """Gelen satiri coz ve dogrula.

    Doner: (veri_dict, hata_mesaji)
    Basarili olursa hata None, basarisizsa veri None.
    """
    if "*" in satir:
        govde, crc_hex = satir.rsplit("*", 1)
        try:
            gelen_crc = int(crc_hex.strip(), 16)
        except ValueError:
            return None, f"CRC okunamadi: {crc_hex!r}"

        hesap_crc = crc16(govde.encode("utf-8"))
        if hesap_crc != gelen_crc:
            return None, f"CRC uyusmuyor (gelen {gelen_crc:04X}, hesap {hesap_crc:04X})"
    else:
        if crc_zorunlu:
            return None, "Pakette CRC yok"
        govde = satir

    try:
        veri = json.loads(govde)
    except json.JSONDecodeError as e:
        return None, f"JSON cozulemedi: {e}"

    if not isinstance(veri, dict):
        return None, "Paket sozluk degil"

    return veri, None


def port_bul():
    """Ground module'un takili oldugu COM portunu otomatik bul."""
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return None
    for p in ports:
        aciklama = (p.description or "").lower()
        if any(k in aciklama for k in
               ("cp210", "ftdi", "ch340", "silicon", "usb serial", "sik")):
            return p.device
    return ports[0].device


class Command(BaseCommand):
    help = "Ground module'den telemetri okur, dogrular ve Django API'ye gonderir."

    def add_arguments(self, parser):
        parser.add_argument("--port", default=None,
                            help="Seri port (orn. COM5). Bos birakilirsa otomatik bulunur.")
        parser.add_argument("--baud", type=int, default=VARSAYILAN_BAUD,
                            help="Seri hiz (varsayilan 115200)")
        parser.add_argument("--url", default=VARSAYILAN_URL,
                            help=f"Django API adresi (varsayilan {VARSAYILAN_URL})")
        parser.add_argument("--crc-yoksay", action="store_true",
                            help="CRC'siz paketleri de kabul et (eski surum testi icin)")

    def handle(self, *args, **secenekler):
        port = secenekler["port"] or port_bul()
        baud = secenekler["baud"]
        url = secenekler["url"]
        crc_zorunlu = not secenekler["crc_yoksay"]

        if not port:
            self.stderr.write(self.style.ERROR(
                "Hic seri port bulunamadi! Ground module takili mi?"))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Dinleniyor: {port} @ {baud} baud\n"
            f"Hedef API : {url}\n"
            f"CRC       : {'zorunlu' if crc_zorunlu else 'opsiyonel'}\n"
            f"Ctrl+C ile cik"))

        # HTTP baglantisini yeniden kullan (her pakette yeni TCP acmamak icin)
        oturum = requests.Session()

        gonderilen = 0
        bozuk_paket = 0
        api_hatasi = 0
        son_paket_zamani = time.time()
        kesinti_bildirildi = False
        api_uyarisi_verildi = False

        ser = None
        try:
            while True:
                # --- Seri baglanti (kopma olursa yeniden dener) ---
                if ser is None:
                    try:
                        ser = serial.Serial(port, baud, timeout=1)
                    except serial.SerialException as e:
                        self.stderr.write(f"Port acilamadi ({e}); 3 sn sonra tekrar...")
                        time.sleep(3)
                        continue

                try:
                    ham = ser.readline()
                except serial.SerialException as e:
                    self.stderr.write(f"Seri hata: {e}; yeniden baglaniliyor...")
                    try:
                        ser.close()
                    except Exception:
                        pass
                    ser = None
                    continue

                # --- Sartname 9.2-d: kesinti suresi takibi ---
                sessizlik = time.time() - son_paket_zamani
                if sessizlik > KESINTI_UYARI_S and not kesinti_bildirildi:
                    self.stderr.write(self.style.WARNING(
                        f"UYARI: {sessizlik:.0f} sn veri yok "
                        f"(sartname siniri {KESINTI_UYARI_S} sn)"))
                    kesinti_bildirildi = True

                if not ham:
                    continue

                metin = ham.decode("utf-8", errors="replace").strip()
                metin = "".join(ch for ch in metin if ch.isprintable())
                if not metin:
                    continue

                # --- Coz ve dogrula ---
                veri, hata = paket_coz(metin, crc_zorunlu)
                if hata:
                    bozuk_paket += 1
                    self.stderr.write(f"[bozuk] {hata}  ({metin[:80]})")
                    continue

                if kesinti_bildirildi:
                    self.stdout.write(self.style.SUCCESS(
                        f"Baglanti geri geldi ({sessizlik:.0f} sn kesinti)"))
                    kesinti_bildirildi = False
                son_paket_zamani = time.time()

                # --- Django API'ye gonder ---
                try:
                    cevap = oturum.post(url, json=veri, timeout=5)
                    if cevap.status_code == 200:
                        gonderilen += 1
                        api_uyarisi_verildi = False
                        self.stdout.write(
                            f"[{gonderilen}] t={veri.get('zaman_ms')}ms  "
                            f"hiz={veri.get('hiz_kmh')} km/h  "
                            f"T={veri.get('T_bat_C')}C  "
                            f"V={veri.get('V_bat_V')}V  "
                            f"E={veri.get('kalan_enerji')}Wh"
                        )
                    else:
                        api_hatasi += 1
                        self.stderr.write(
                            f"API {cevap.status_code}: {cevap.text[:200]}")
                except requests.exceptions.ConnectionError:
                    api_hatasi += 1
                    if not api_uyarisi_verildi:
                        self.stderr.write(self.style.ERROR(
                            f"Django sunucusuna baglanilamiyor ({url})\n"
                            f"  -> Baska bir terminalde 'python manage.py runserver' "
                            f"calisiyor mu?"))
                        api_uyarisi_verildi = True
                except requests.exceptions.RequestException as e:
                    api_hatasi += 1
                    self.stderr.write(f"API hatasi: {e}")

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING(
                f"\nDurduruldu.  Gonderilen: {gonderilen}  "
                f"Bozuk paket: {bozuk_paket}  API hatasi: {api_hatasi}"
            ))
        finally:
            if ser is not None:
                try:
                    ser.close()
                except Exception:
                    pass
            oturum.close()
