from django.db import models


class TelemetriKayit(models.Model):
    """Aractan gelen telemetri ornegi.

    Sensor alanlari null olabilir: BMS baglantisi koptugunda arac
    bayat deger gondermek yerine bos gonderir (sartname 9.2-e).
    Boylece kayitta "veri yoktu" ile "deger sifirdi" ayirt edilir.
    """

    zaman_ms     = models.BigIntegerField()
    hiz_kmh      = models.FloatField(null=True, blank=True)
    T_bat_C      = models.FloatField(null=True, blank=True)
    V_bat_V      = models.FloatField(null=True, blank=True)
    kalan_enerji = models.FloatField(null=True, blank=True)
    sunucu_zaman = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['zaman_ms']

    def __str__(self):
        return (f"{self.zaman_ms} ms | {self.hiz_kmh} km/h | "
                f"{self.T_bat_C} C | {self.V_bat_V} V")
