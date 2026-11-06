import hashlib
import uuid

from ..models import AccesoQR, Lugar


def identificar_y_registrar_acceso_qr(token, ip, user_agent):
    token_texto = str(token or '').strip()[:256]
    token_huella = hashlib.sha256(token_texto.lower().encode('utf-8')).hexdigest()
    try:
        token_uuid = uuid.UUID(token_texto)
    except (AttributeError, TypeError, ValueError):
        token_uuid = None
    lugar = None
    if token_uuid is not None:
        lugar = Lugar.objects.filter(qr_token=token_uuid).only('id', 'nombre_del_lugar', 'qr_token', 'qr_activo', 'visibilidad_qr').first()
    if lugar is None:
        resultado = AccesoQR.Resultado.INVALIDO
    elif not lugar.qr_activo:
        resultado = AccesoQR.Resultado.DESACTIVADO
    else:
        resultado = AccesoQR.Resultado.DENEGADO
    acceso = AccesoQR.objects.create(lugar=lugar, ip=ip or None, user_agent=(user_agent or '')[:512], token_huella=token_huella, resultado=resultado)
    return (lugar, acceso)


def marcar_acceso_permitido(acceso):
    acceso.resultado = AccesoQR.Resultado.PERMITIDO
    acceso.save(update_fields=["resultado"])
