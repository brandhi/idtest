from django.shortcuts import render
from .services import CensusService
import os
from django.http import FileResponse, Http404
from django.conf import settings

def vista_poblacion_femenina(request):
    limit = request.GET.get('limit', 10)
    data = CensusService.get_female_population(limit=int(limit))
    return render(request, 'census/inciso_a.html', {'resultados': data, 'limit': limit})

def vista_discapacidad(request):
    data = CensusService.get_disability_by_state()
    return render(request, 'census/inciso_b.html', {'resultados': data})

def vista_demograficos(request):
    data = CensusService.get_demographics()
    return render(request, 'census/inciso_c.html', {'resultados': data})

def home_view(request):
    return render(request, 'census/home.html')

def download_etl_file(request, filename):
    # Construimos la ruta absoluta hacia la carpeta etl/DATA
    data_dir = os.path.join(settings.BASE_DIR, 'etl', 'DATA')
    file_path = os.path.join(data_dir, filename)

    # Validamos que el archivo exista y pertenezca al directorio destino (seguridad)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        response = FileResponse(open(file_path, 'rb'), as_attachment=True)
        return response
    else:
        raise Http404("El archivo solicitado no existe.")