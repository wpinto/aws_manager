import boto3
import keys as keys

region_name = keys.region_name

def crear_sesion(ambiente):
    key = 'aws_access_key_id_' + str(ambiente)
    secret = 'aws_secret_access_key_' + str(ambiente)

    return boto3.Session(
        aws_access_key_id=keys.__dict__[key],
        aws_secret_access_key=keys.__dict__[secret],
        region_name=region_name
    )


# --- Crear cliente EC2 ---
def crear_cliente(sesion,servicio):
    return sesion.client(servicio)


def crear(servicio, ambiente):
    sesion = crear_sesion(ambiente)
    cliente = crear_cliente(sesion,servicio)
    return cliente
