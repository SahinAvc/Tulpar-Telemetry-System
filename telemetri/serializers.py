from rest_framework import serializers

from .models import TelemetriKayit


class TelemetriSerializer(serializers.ModelSerializer):
    """Aractan gelen paketi dogrular.

    Sensor alanlari None gelebilir (BMS baglantisi kopukken).
    zaman_ms her zaman zorunludur.
    """

    hiz_kmh      = serializers.FloatField(required=False, allow_null=True)
    T_bat_C      = serializers.FloatField(required=False, allow_null=True)
    V_bat_V      = serializers.FloatField(required=False, allow_null=True)
    kalan_enerji = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model  = TelemetriKayit
        fields = ['zaman_ms', 'hiz_kmh', 'T_bat_C', 'V_bat_V', 'kalan_enerji']
