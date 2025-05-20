from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.index, name='login'),
    # puedes añadir más rutas aquí
]
