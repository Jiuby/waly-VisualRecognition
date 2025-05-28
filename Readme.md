# 📷 Waly - Sistema de Reconocimiento Facial para Control de Acceso

Proyecto desarrollado durante la Hackathon "DataHack" - Reto 2: Optimización del control de acceso y gestión de usuarios en campus educativos.

---

## 🚀 Descripción

**Waly** es una aplicación web construida con **Django** que:
- Registra entradas y salidas mediante **reconocimiento facial**
- Permite la gestión de usuarios y eventos del campus
- Visualiza datos y patrones de acceso

Utiliza `dlib` y `face_recognition`, junto con `OpenCV`, para detectar rostros en tiempo real a través de una cámara.

---

## ⚙️ Requisitos del Sistema


### ✅ En Windows (modo local)
- Python 3.8.10
- Pip
- Visual Studio Build Tools  
  - Instalar el paquete: **Desktop Development with C++**
- Git (opcional)
- dlib
- CMake



---

## 🛠️ Instalación y Ejecución

### 🔧 Opción 1: Ejecutar en Windows (modo local)

1. Clona este repositorio:
   ```bash
   git clone https://github.com/tuusuario/waly.git
   cd waly
    ```
2. Crea un entorno virtual:
    ```python -m venv venv
    venv\Scripts\activate
    ```
3. Instala las dependencias:
    ```bash
   pip install --upgrade pip
    pip install -r requirements.txt
    ```
4. Ejecuta las migraciones:
    ```bash
    python manage.py migrate
     ```
5 Ejecuta el servidor
    ```
    python manage.py runserver
    ```

el login no es funcional asi que le puedes dar a login para continuar

