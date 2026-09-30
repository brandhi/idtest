from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('inciso-a/', views.vista_poblacion_femenina, name='inciso_a'),
    path('inciso-b/', views.vista_discapacidad, name='inciso_b'),
    path('inciso-c/', views.vista_demograficos, name='inciso_c'),
    path('download/<str:filename>/', views.download_etl_file, name='download_etl_file'),
]