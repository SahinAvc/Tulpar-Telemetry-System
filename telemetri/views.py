from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from .models import TelemetriKayit
from .serializers import TelemetriSerializer
from .utils import kayit_isle

class TelemetriAlView(APIView):
    def post(self, request):
        ok, hata = kayit_isle(request.data)
        if ok:
            return Response({"durum": "OK"})
        print("Hata:", hata)
        return Response(hata, status=400)

def dashboard(request):
    return render(request, 'dashboard.html')