from django.urls import path
from . import views

from django.urls import path
from . import views

urlpatterns = [
    path("RegistrarEntrada/", views.registrar_entrada, name="registrar_entrada"),
    path('verify-face/', views.verify_face, name='verify-face'),

    path("RegistrarSalida/", views.registrar_salida, name="registrar_salida"),
]