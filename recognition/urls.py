from django.urls import path
from . import views

urlpatterns = [
    # Pantalla de cámara modo ENTRADA
    path("RegistrarEntrada/", views.registrar_entrada, name="registrar_entrada"),

    # Pantalla de cámara modo SALIDA  (usa misma función minúscula)
    path("RegistrarSalida/",  views.registrar_salida,  name="registrar_salida"),

    # El POST lo recibe la misma URL (registrar_salida); no hace falta otra ruta.
    path("verify-face/",      views.verify_face,       name="verify-face"),
    path("RegistrarUsuario/", views.registrar_usuario, name="RegistrarUsuario"),
]
