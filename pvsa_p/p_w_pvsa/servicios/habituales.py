import hashlib
from django.core.exceptions import ValidationError
from django.db.models import Q
from ..models import CategoriaObjeto, Objeto, TipoObjeto, TipoLugarObjetoTipico

TIPICOS_POR_TIPO_LUGAR = {
    "Baño": {
        "Infraestructura": [
            "Paredes", "Piso", "Cielo", "Techo", "Luces" ,"Ventanas", "Puertas",
            "Conexión eléctrica", "Interruptores"
        ],
        "Sanitario": [
            "Tasas", "Urinario","Desagües","Papeleros","Lavamanos"
        ],
        "Decoración":[
            "Espejos",
        ],
        "Higiene":[
            "Jaboneras","Dispensadores de papel", "Dispensadores de jabón"
        ],
    },
    "Vestidor": {
        "Infraestructura": [
            "Paredes", "Piso", "Cielo", "Techo", "Luces" ,"Ventanas", "Puertas",
            "Conexión eléctrica", "Interruptores"
        ],
        "Mobiliario": [
            "Bancos", "Casilleros", "Percheros",
        ],
        "Sanitario":[
            "Duchas",
        ],
        "Higiene":[
            "Secadores de toalla","Dispensadores de jabón"
        ],
        "Climatización":[
            "Extractores","Estufas"
        ],
    },
    "Comedor": {
        "Infraestructura": [
            "Paredes", "Piso", "Cielo", "Techo", "Luces" ,"Ventanas", "Puertas",
            "Conexión eléctrica", "Interruptores"
        ],
        "Mobiliario":[
            "Mesas","Sillas","Muebles"
        ],
        "Electrodomésticos": [
            "Refrigerador","Microondas","Dispensador de agua","Televisor",
        ],
        "Sanitario":[
            "Lavaplatos","Papeleros"
        ],
        "Climatización":[
            "Aire acondicionado"
        ],
    },
    "Cafetería":{
        "Infraestructura": [
            "Paredes", "Piso", "Cielo", "Techo", "Luces" ,"Ventanas", "Puertas",
            "Conexión eléctrica", "Interruptores"
        ],
        "Mobiliario":[
            "Mesas","Sillas","Muebles"
        ],
        "Electrodomésticos":[
            "Cafetera","Refrigerador","Dispensador de agua"
        ],
        "Climatización":[
            "Aire acondicionado"
        ],
    },
    "Baño vestidor":{
        "Infraestructura": [
            "Paredes", "Piso", "Cielo", "Techo", "Luces" ,"Ventanas", "Puertas",
            "Conexión eléctrica", "Interruptores"
        ],
        "Sanitario": [
            "Tasas", "Urinario","Desagües","Lavamanos","Duchas","Papeleros"
        ],
        "Decoración":[
            "Espejos",
        ],
        "Higiene":[
            "Secadores de toalla", "Dispensadores de jabón"
        ],
        "Mobiliario":[
            "Bancas","Casilleros",
        ],
        "Climatización":[
            "Extractores"
        ],
    }
}



def sugerencias_habituales(tipo_lugar):
    relaciones = list(TipoLugarObjetoTipico.objects.filter(tipo_lugar=tipo_lugar, activo=True)
        .select_related("tipo_objeto__objeto__objeto_categoria")
        .order_by("orden", "tipo_objeto__objeto__objeto_categoria__nombre_de_categoria",
                  "tipo_objeto__objeto__nombre_del_objeto", "tipo_objeto__marca", "tipo_objeto__material"))
    if relaciones:
        resultado = []
        for relacion in relaciones:
            variante = relacion.tipo_objeto
            objeto = variante.objeto
            categoria = objeto.objeto_categoria
            marca = (variante.marca or "").strip()
            material = (variante.material or "").strip()
            detalles = f" ({marca} {material})".strip() if marca or material else ""
            resultado.append({"categoria_id": categoria.pk, "objeto_id": objeto.pk,
                "tipo_objeto_id": variante.pk,
                "label": f"{categoria.nombre_de_categoria} - {objeto.nombre_del_objeto}{detalles}"})
        return resultado
    catalogo = TIPICOS_POR_TIPO_LUGAR.get(tipo_lugar.tipo_de_lugar, {})
    if not catalogo:
        return []
    nombres_objetos = [nombre for nombres in catalogo.values() for nombre in nombres]
    objetos = {objeto.nombre_del_objeto: objeto for objeto in Objeto.objects
        .filter(nombre_del_objeto__in=nombres_objetos).select_related("objeto_categoria")}
    categorias = {categoria.nombre_de_categoria: categoria for categoria in CategoriaObjeto.objects
        .filter(nombre_de_categoria__in=catalogo)}
    variantes = {}
    for variante in TipoObjeto.objects.filter(objeto_id__in=[objeto.pk for objeto in objetos.values()]).filter(
            Q(marca="") | Q(marca__isnull=True)).filter(
            Q(material="") | Q(material__isnull=True)).order_by("pk"):
        variantes.setdefault(variante.objeto_id, variante)
    resultado = []
    for nombre_categoria, nombres in catalogo.items():
        for nombre in nombres:
            objeto = objetos.get(nombre)
            categoria = objeto.objeto_categoria if objeto else categorias.get(nombre_categoria)
            variante = variantes.get(objeto.pk) if objeto else None
            clave = hashlib.sha256(f"{nombre_categoria}\0{nombre}".encode()).hexdigest()[:24]
            categoria_nombre = categoria.nombre_de_categoria if categoria else nombre_categoria
            resultado.append({"categoria_id": categoria.pk if categoria else None,
                "objeto_id": objeto.pk if objeto else None, "tipo_objeto_id": variante.pk if variante else None,
                "label": f"{categoria_nombre} - {nombre}",
                "referencia": f"habitual:{tipo_lugar.pk}:{clave}",
                "categoria_nombre": categoria_nombre, "objeto_nombre": nombre,
                "virtual": variante is None})
    return resultado


def resolver_sugerencia(referencia, tipo_lugar):
    if tipo_lugar is not None and referencia.startswith(f"habitual:{tipo_lugar.pk}:"):
        if not hasattr(tipo_lugar, "_sugerencias_validas"):
            tipo_lugar._sugerencias_validas = {item.get("referencia"): item for item in sugerencias_habituales(tipo_lugar)}
        if referencia in tipo_lugar._sugerencias_validas:
            return tipo_lugar._sugerencias_validas[referencia]
    raise ValidationError("La sugerencia no corresponde al tipo de lugar seleccionado.")


def materializar_sugerencia(sugerencia):
    objeto = Objeto.objects.select_for_update().filter(nombre_del_objeto=sugerencia["objeto_nombre"]).first()
    if objeto is None:
        categoria, _ = CategoriaObjeto.objects.get_or_create(nombre_de_categoria=sugerencia["categoria_nombre"])
        objeto, _ = Objeto.objects.get_or_create(nombre_del_objeto=sugerencia["objeto_nombre"], defaults={"objeto_categoria": categoria})
        objeto = Objeto.objects.select_for_update().get(pk=objeto.pk)
    if objeto.objeto_categoria.nombre_de_categoria != sugerencia["categoria_nombre"]:
        raise ValidationError("La categoría del objeto sugerido cambió. Revisa el formulario.")
    variante = TipoObjeto.objects.filter(objeto=objeto).filter(
        Q(marca="") | Q(marca__isnull=True)).filter(
        Q(material="") | Q(material__isnull=True)).order_by("pk").first()
    if variante is None:
        variante = TipoObjeto.objects.create(objeto=objeto, marca="", material="")
    return objeto.objeto_categoria, objeto, variante
