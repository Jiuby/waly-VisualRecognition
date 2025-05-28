import os
import cv2
import pickle
import time
import numpy as np
import insightface
from sklearn.preprocessing import normalize
from tqdm import tqdm

# Calcula la raíz de tu proyecto (donde está manage.py)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Carpeta donde están tus imágenes (ajusta si difiere)
image_folder = os.path.join(BASE_DIR, 'facialRecognition', 'faces')

# Dónde quieres guardar el embeddings.pkl
output_path = os.path.join(BASE_DIR, 'facialRecognition', 'embeddings.pkl')

# Inicializa InsightFace
model = insightface.app.FaceAnalysis(allowed_modules=['detection','recognition'])
model.prepare(ctx_id=-1)

def load_images_and_extract_embeddings(folder):
    embeddings, labels = [], []
    for fn in tqdm(os.listdir(folder), desc="Extrayendo embeddings"):
        path = os.path.join(folder, fn)
        img = cv2.imread(path)
        if img is None: continue

        for face in model.get(img):
            if face.embedding is not None:
                embeddings.append(face.embedding)
                # parsea nombre e ID
                name_id, _ = os.path.splitext(fn)
                parts = name_id.rsplit('_',1)
                name = parts[0].replace('_',' ')
                uid  = parts[1] if len(parts)==2 else ''
                labels.append({'name':name, 'id':uid})

    return np.array(embeddings), labels

if __name__ == "__main__":
    t0 = time.time()
    embs, labs = load_images_and_extract_embeddings(image_folder)
    print(f"→ Extracción terminada en {time.time()-t0:.2f}s")

    embs = normalize(embs)
    with open(output_path, 'wb') as f:
        pickle.dump({'embeddings': embs, 'labels': labs}, f)
    print(f"→ Embeddings guardados en {output_path}")
