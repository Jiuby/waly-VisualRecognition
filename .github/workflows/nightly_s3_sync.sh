#!/usr/bin/env bash
#
# Borra todo el prefijo faces/ del bucket y vuelve a subir
# el contenido local de ./facialRecognition/faces

set -e                          # abortar si algo falla

### CONFIGURA ESTAS 3 VARIABLES ###
AWS_PROFILE="default"           # o deja vacío si usas variables de entorno
AWS_REGION="us-east-1"
BUCKET="hackathon-facesiupb"
###################################

LOCAL_DIR="./facialRecognition/faces"
PREFIX="faces"                  # subcarpeta dentro del bucket

echo "⏱  $(date)  –  limpieza S3…"
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" \
    s3 rm "s3://$BUCKET/$PREFIX/" --recursive || true

echo "⬆️  subiendo nuevas imágenes…"
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" \
    s3 sync "$LOCAL_DIR" "s3://$BUCKET/$PREFIX/" \
            --exclude "*" --include "*.jpg" --include "*.jpeg" --include "*.png"

echo "✅ Sincronización completa"
