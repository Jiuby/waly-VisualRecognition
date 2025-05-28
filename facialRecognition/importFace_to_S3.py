#!/usr/bin/env python3
import os
import sys
import mimetypes
import boto3
from decouple import config  # o usa django-environ según prefieras

# --- lee las vars desde el .env ---
AWS_ACCESS_KEY_ID     = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_REGION            = config('AWS_REGION')
S3_BUCKET             = config('S3_BUCKET')

def upload_faces(folder_path):
    """
    Recorre `folder_path` y sube todos los .jpg/.jpeg/.png
    al bucket en la carpeta 'faces/', preservando subdirectorios.
    """
    session = boto3.Session(
        aws_access_key_id     = AWS_ACCESS_KEY_ID,
        aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
        region_name           = AWS_REGION
    )
    s3 = session.client('s3')

    for root, _, files in os.walk(folder_path):
        for fn in files:
            if fn.lower().endswith(('.jpg', '.jpeg', '.png')):
                local_path = os.path.join(root, fn)
                rel_path   = os.path.relpath(local_path, folder_path)
                s3_key     = f"faces/{rel_path.replace(os.sep, '/')}"

                # Detecta tipo MIME
                content_type, _ = mimetypes.guess_type(local_path)
                extra_args = {}
                if content_type:
                    extra_args['ContentType'] = content_type

                # Sube sin ACL
                s3.upload_file(
                    Filename=local_path,
                    Bucket=S3_BUCKET,
                    Key=s3_key,
                    ExtraArgs=extra_args
                )
                print(f"✔ Uploaded {local_path} → s3://{S3_BUCKET}/{s3_key}")

if __name__ == '__main__':
    folder = sys.argv[1] if len(sys.argv) > 1 else 'faces'
    if not os.path.isdir(folder):
        print(f"ERROR: carpeta no encontrada '{folder}'")
        sys.exit(1)
    upload_faces(folder)
