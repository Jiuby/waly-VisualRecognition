import os
import cv2
import pickle
import numpy as np
from insightface import app
from sklearn.preprocessing import normalize

# ————————————————————————————————————————————
#  Carga de embeddings y etiquetas
# ————————————————————————————————————————————
BASE_DIR    = os.path.dirname(os.path.dirname(__file__))
EMB_PATH    = os.path.join(BASE_DIR, 'facialRecognition', 'embeddings.pkl')
with open(EMB_PATH, 'rb') as f:
    data         = pickle.load(f)
    known_embs   = data['embeddings']
    known_labels = data['labels']

# Normalizamos los embeddings
known_embs = normalize(known_embs)

# ————————————————————————————————————————————
#  Inicialización del modelo ArcFace (InsightFace)
# ————————————————————————————————————————————
model = app.FaceAnalysis(allowed_modules=['detection', 'recognition'])
model.prepare(ctx_id=-1)


def recognize_frame(frame, threshold=0.6):
    """
    Detecta en un solo frame, extrae embedding y compara contra la base.
    Devuelve (label, score) si score>=threshold, o None.
    """
    # 1) Detectar y extraer embedding
    faces = model.get(frame)
    if not faces:
        return None

    emb = faces[0].embedding
    emb = emb / np.linalg.norm(emb)

    # 2) Comparar contra la base
    sims = known_embs.dot(emb)
    best_idx   = int(np.argmax(sims))
    best_score = float(sims[best_idx])

    # 3) Verificar umbral
    if best_score >= threshold:
        return known_labels[best_idx], best_score
    return None
