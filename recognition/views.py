import os
import pickle

import cv2
import numpy as np
import insightface
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .utils import recognize_frame

# ——————————————————————————————————————————————————————
#  Carga global del modelo y de los embeddings pre-extraídos
# ——————————————————————————————————————————————————————
# Inicializa ArcFace
model = insightface.app.FaceAnalysis(allowed_modules=['detection', 'recognition'])
model.prepare(ctx_id=-1)

# Ruta de tu embeddings.pkl dentro de facialRecognition/
EMB_PATH = os.path.join(settings.BASE_DIR,
                        'facialRecognition',
                        'embeddings.pkl')

with open(EMB_PATH, 'rb') as f:
    data = pickle.load(f)
known_embs = data['embeddings']    # numpy array (normalizado)
known_labels = data['labels']      # lista de dicts {name, id}
sidebarItems = [
    {"name": "Menú Principal"},
    {
        "name": "Dashboard",
        "url": "/accounts/index/",
        "icon": "grid-fill",
        "key": "dashboard",
        "submenu": []
    },
    {

        "name": "Registro",
        "url": None,
        "icon": "people-fill",
        "key": "users",
        "submenu": [
            {"name": "Registrar Entrada", "isTitle": True, "url": "/recognition/RegistrarEntrada/"},
            {"name": "Registrar salida", "url": "/recognition/RegistrarSalida/"}
        ]
    }
]

def registrar_entrada(request):
    return render(request,
                  'RegistrarEntrada.html',
                  {
                      "title": "Registrar Entrada",
                      "web_title": "Mazer",
                      "current_url": request.path,
                      "sidebarItems": sidebarItems,  # si lo necesitas
                  })

def registrar_salida(request):
    return render(request, 'RegistrarSalida.html', {
        "title":        "Registrar Salida",
        "web_title":    "Mazer",
        "current_url":  request.path,
        "sidebarItems": sidebarItems,
    })

# ——————————————————————————————————————————————————————
#  AJAX endpoint que recibe el snapshot y verifica el rostro
# ——————————————————————————————————————————————————————
@csrf_exempt
def verify_face(request):
    if request.method != 'POST':
        return JsonResponse({'status':'error','msg':'Sólo POST'}, status=400)

    # Leer solo el primer snapshot enviado
    files = list(request.FILES.values())
    if not files:
        return JsonResponse({'status':'fail','msg':'no snapshot'}, status=200)

    # Decodificar blob a imagen OpenCV
    arr = np.frombuffer(files[0].read(), np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return JsonResponse({'status':'fail','msg':'invalid image'}, status=200)

    # Ejecutar reconocimiento
    result = recognize_frame(frame, threshold=0.6)
    if result:
        label, score = result
        name, uid = (label.split('_',1) if isinstance(label,str) and '_' in label
                     else (label.get('name',''), label.get('id','')))

        print(f"[verify-face] Reconocido: {name} ({uid}), score={score:.3f}")
        return JsonResponse({
            'status': 'ok',
            'name':   name,
            'id':     uid,
            'score':  round(score,3)
        })
    else:
        print("[verify-face] No reconocido")
        return JsonResponse({
            'status': 'fail',
            'name':   None,
            'id':     None,
            'score':  0.0
        }, status=200)