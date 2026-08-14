from django.urls import path
from . import views

urlpatterns = [
    path('api/telemetri/', views.TelemetriAlView.as_view()),
    path('', views.dashboard),
]