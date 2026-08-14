from django.urls import path
from .consumers import TelemetriConsumer

websocket_urlpatterns = [
    path('ws/telemetri/', TelemetriConsumer.as_asgi()),
]