import boto3
from django.conf import settings
from boto3.dynamodb.conditions import Key


def get_dynamo_table():
    dynamo = boto3.resource(
        'dynamodb',
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    return dynamo.Table("Eventos")

def put_evento(item):
    """
    item = {
      'fecha': '2025-05-21',       # YYYY-MM-DD
      'hora_inicio': '14:00',
      'hora_fin': '15:30',
      'titulo': 'Reunión',
      'descripcion': '…'
    }
    """
    table = get_dynamo_table()
    table.put_item(Item=item)

def get_eventos_mes(year, month):
    """
    Asume que tu tabla tiene un índice secundario global (GSI)
    con partition_key = 'fecha' (YYYY-MM-DD).
    Aquí hacemos scan y filtramos, o mejor: crea un GSI por 'YYYY-MM'.
    Para simplificar, hago scan:
    """
    table = get_dynamo_table()
    resp = table.scan()
    items = resp['Items']
    # Filtrar sólo los del mes
    prefix = f"{year:04d}-{month:02d}-"
    return [i for i in items if i['fecha'].startswith(prefix)]
