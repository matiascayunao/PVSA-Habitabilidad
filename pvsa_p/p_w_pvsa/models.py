import uuid

from django.conf import settings

from .private_storage import EvidenciaPrivadaStorage

from django.core.exceptions import ValidationError

from django.db import models, transaction





# =========================================================

# ESTRUCTURA FÍSICA

# =========================================================



class Sector(models.Model):

    sector = models.CharField(max_length=100, unique=True)



    def __str__(self):

        return self.sector





class Ubicacion(models.Model):

    ubicacion = models.CharField(max_length=100, unique=True)



    sector = models.ForeignKey(

        Sector,

        verbose_name="sector",

        on_delete=models.RESTRICT,

    )



    def __str__(self):

        return f"{self.ubicacion} | Sector: {self.sector.sector}"





class Piso(models.Model):

    piso = models.SmallIntegerField()



    ubicacion = models.ForeignKey(

        Ubicacion,

        verbose_name="ubicacion",

        on_delete=models.RESTRICT,

    )



    def __str__(self):

        return f"Piso {self.piso} | {self.ubicacion.ubicacion}"





class TipoLugar(models.Model):

    tipo_de_lugar = models.CharField(

        max_length=100,

        unique=True,

    )



    def __str__(self):

        return self.tipo_de_lugar





class Lugar(models.Model):

    nombre_del_lugar = models.CharField(max_length=100)



    piso = models.ForeignKey(

        Piso,

        verbose_name="piso",

        on_delete=models.RESTRICT,

    )



    lugar_tipo_lugar = models.ForeignKey(

        TipoLugar,

        verbose_name="tipo de lugar",

        on_delete=models.RESTRICT,

    )



    # Identificador público aleatorio. No reemplaza la clave primaria del lugar.

    # Los lugares existentes requieren una migración de datos por etapas.

    qr_token = models.UUIDField(

        default=uuid.uuid4,

        unique=True,

        editable=False,

        verbose_name="token QR",

    )



    # Se habilitará explícitamente desde la administración QR.

    # editable=False lo excluye de formularios genéricos del lugar.

    qr_activo = models.BooleanField(

        default=False,

        editable=False,

        verbose_name="QR activo",

    )



    # Define qué puede hacer una persona al escanear el QR.

    # Por seguridad, todos los lugares son privados inicialmente.

    visibilidad_qr = models.CharField(

        max_length=10,

        choices=[

            ("privado", "Privado: requiere iniciar sesión"),

            ("publico", "Público: permite reportar sin cuenta"),

        ],

        default="privado",

        editable=False,

        verbose_name="visibilidad del QR",

    )



    # Clasificación física del lugar.

    # No determina los permisos individuales de los usuarios.

    es_area_comun = models.BooleanField(

        default=False,

        verbose_name="¿Es un área común?",

        help_text=(

            "Ejemplo: baños, comedores y vestidores. "

            "Al crear el lugar, el QR será público "

            "automáticamente."

        ),

    )





    def save(self, *args, **kwargs):



        # Aplicar la configuración automática

        # solamente cuando se crea un lugar nuevo.

        if self._state.adding:



            if self.es_area_comun:

                self.visibilidad_qr = "publico"

            else:

                self.visibilidad_qr = "privado"



            # Los lugares nuevos tendrán su QR habilitado.

            self.qr_activo = True



        # Guardar el lugar normalmente.

        super().save(*args, **kwargs)







    def __str__(self):

        return (

            f"{self.nombre_del_lugar} | "

            f"Piso {self.piso.piso} | "

            f"{self.piso.ubicacion.ubicacion}"

        )



    @property

    def operatividad_lugar(self):

        """

        Calcula la operatividad general del lugar

        ponderando la operatividad de cada objeto

        según su importancia.

        """



        objetos = list(self.objetos_lugar.all())



        if not objetos:

            return 100.0



        suma_ponderada = 0

        suma_importancias = 0



        for obj in objetos:

            importancia = obj.importancia or 1



            suma_ponderada += (

                obj.operatividad_objeto * importancia

            )



            suma_importancias += importancia



        if suma_importancias == 0:

            return 100.0



        return round(

            suma_ponderada / suma_importancias,

            1,

        )





# =========================================================

# CATÁLOGO DE OBJETOS

# =========================================================



class CategoriaObjeto(models.Model):

    nombre_de_categoria = models.CharField(

        max_length=100,

        verbose_name="categoría",

        unique=True,

    )



    def __str__(self):

        return self.nombre_de_categoria





class Objeto(models.Model):

    nombre_del_objeto = models.CharField(

        max_length=100,

        verbose_name="objeto",

        unique=True,

    )



    objeto_categoria = models.ForeignKey(

        CategoriaObjeto,

        verbose_name="categoria",

        on_delete=models.RESTRICT,

    )



    def __str__(self):

        return (

            f"{self.nombre_del_objeto} "

            f"({self.objeto_categoria.nombre_de_categoria})"

        )





class TipoObjeto(models.Model):

    objeto = models.ForeignKey(

        Objeto,

        verbose_name="objeto",

        on_delete=models.RESTRICT,

    )



    marca = models.CharField(

        max_length=100,

        verbose_name="marca",

        blank=True,

        null=True,

    )



    material = models.CharField(

        max_length=100,

        verbose_name="material",

        blank=True,

        null=True,

    )



    def __str__(self):

        marca_txt = (self.marca or "").strip()

        material_txt = (self.material or "").strip()



        detalles = " ".join(

            texto

            for texto in [marca_txt, material_txt]

            if texto

        )



        if detalles:

            return f"{self.objeto.nombre_del_objeto} - {detalles}"



        return self.objeto.nombre_del_objeto





# =========================================================

# OBJETOS TÍPICOS SEGÚN TIPO DE LUGAR

# =========================================================



class TipoLugarObjetoTipico(models.Model):

    tipo_lugar = models.ForeignKey(

        TipoLugar,

        verbose_name="tipo de lugar",

        on_delete=models.CASCADE,

        related_name="tipicos",

    )



    tipo_objeto = models.ForeignKey(

        TipoObjeto,

        verbose_name="tipo de objeto",

        on_delete=models.CASCADE,

        related_name="tipico_en",

    )



    activo = models.BooleanField(default=True)



    orden = models.PositiveSmallIntegerField(

        default=0,

    )



    importancia = models.PositiveSmallIntegerField(

        default=1,

        choices=(

            (1, "Baja"),

            (2, "Media"),

            (3, "Alta"),

        ),

    )



    class Meta:

        unique_together = (

            "tipo_lugar",

            "tipo_objeto",

        )



        ordering = (

            "orden",

            "id",

        )



    def __str__(self):

        return (

            f"{self.tipo_lugar.tipo_de_lugar} "

            f"-> {self.tipo_objeto}"

        )





# =========================================================

# OBJETOS REGISTRADOS EN CADA LUGAR

# =========================================================



class ObjetoLugar(models.Model):



    ESTADO = (

        ("B", "Todo bueno"),

        ("P", "Con pendientes"),

        ("M", "Con unidades malas"),

    )



    IMPORTANCIA = (

        (1, "Baja"),

        (2, "Media"),

        (3, "Alta / Crítica"),

    )



    cantidad = models.SmallIntegerField()



    estado = models.CharField(

        max_length=1,

        choices=ESTADO,

        default="B",

    )



    detalle = models.CharField(

        max_length=200,

        blank=True,

    )



    fecha = models.DateField(

        auto_now_add=True,

    )



    importancia = models.PositiveSmallIntegerField(

        default=1,

        choices=IMPORTANCIA,

    )



    cantidad_mala = models.SmallIntegerField(

        default=0,

    )



    cantidad_pendiente = models.SmallIntegerField(

        default=0,

    )



    minimo_operativo = models.SmallIntegerField(

        default=1,

        help_text=(

            "Cantidad mínima que debe estar funcionando "

            "para considerar aceptable este objeto."

        ),

    )



    lugar = models.ForeignKey(

        Lugar,

        verbose_name="lugar",

        on_delete=models.RESTRICT,

        related_name="objetos_lugar",

        null=True,

        blank=True,

    )



    tipo_de_objeto = models.ForeignKey(

        TipoObjeto,

        verbose_name="tipo de objeto",

        on_delete=models.RESTRICT,

        related_name="objetos_lugar",

        null=True,

        blank=True,

    )



    def __str__(self):

        if self.lugar:

            lugar_txt = (

                f"{self.lugar.nombre_del_lugar} | "

                f"Piso {self.lugar.piso.piso} | "

                f"{self.lugar.piso.ubicacion.ubicacion}"

            )

        else:

            lugar_txt = "Sin lugar asignado"



        if self.tipo_de_objeto and self.tipo_de_objeto.objeto:

            objeto_txt = (

                self.tipo_de_objeto.objeto.nombre_del_objeto

            )



            marca_txt = (

                self.tipo_de_objeto.marca

                or "Sin marca"

            )



            material_txt = (

                self.tipo_de_objeto.material

                or "Sin material"

            )



        else:

            objeto_txt = "Objeto no especificado"

            marca_txt = "Sin marca"

            material_txt = "Sin material"



        return (

            f"{objeto_txt} - "

            f"{marca_txt} {material_txt} "

            f"en {lugar_txt} "

            f"(total {self.cantidad}, "

            f"condición {self.get_estado_display()})"

        )



    # -----------------------------------------------------

    # CANTIDADES

    # -----------------------------------------------------



    @property

    def cantidad_buena(self):

        cantidad = self.cantidad or 0

        malas = self.cantidad_mala or 0

        pendientes = self.cantidad_pendiente or 0



        buenas = cantidad - malas - pendientes



        return max(buenas, 0)



    @property

    def unidades_funcionales_equivalentes(self):

        """

        Valor funcional utilizado para calcular operatividad:



        - Unidad buena      = 1

        - Unidad pendiente  = 0.5

        - Unidad mala       = 0

        """



        cantidad = self.cantidad or 0

        malas = self.cantidad_mala or 0

        pendientes = self.cantidad_pendiente or 0



        equivalentes = (

            cantidad

            - malas

            - (pendientes * 0.5)

        )



        return max(equivalentes, 0)



    # -----------------------------------------------------

    # OPERATIVIDAD

    # -----------------------------------------------------



    @property

    def operatividad_objeto(self):

        """

        Calcula la operatividad del objeto considerando:



        - cantidad total

        - unidades malas

        - unidades pendientes

        - mínimo operativo



        Bajo el mínimo operativo:

            0% a 50%



        Cumpliendo el mínimo:

            50%



        Sobre el mínimo:

            50% a 100%

        """



        cantidad = self.cantidad or 0



        if cantidad <= 0:

            return 0.0



        minimo = self.minimo_operativo or 1



        if minimo < 1:

            minimo = 1



        if minimo > cantidad:

            minimo = cantidad



        funcionales = (

            self.unidades_funcionales_equivalentes

        )



        if funcionales <= 0:

            return 0.0



        if funcionales < minimo:

            resultado = (

                funcionales / minimo

            ) * 50



            return round(resultado, 1)



        if cantidad == minimo:

            resultado = (

                funcionales / cantidad

            ) * 100



            return round(resultado, 1)



        resultado = 50 + (

            (

                funcionales - minimo

            )

            /

            (

                cantidad - minimo

            )

        ) * 50



        resultado = min(resultado, 100)



        return round(resultado, 1)



    # -----------------------------------------------------

    # CONDICIÓN AUTOMÁTICA

    # -----------------------------------------------------



    @staticmethod

    def calcular_estado(

        cantidad_mala,

        cantidad_pendiente,

    ):

        """

        Calcula la condición según las cantidades.



        M = existe al menos una unidad mala

        P = no hay malas pero sí pendientes

        B = todas las unidades están buenas

        """



        cantidad_mala = cantidad_mala or 0

        cantidad_pendiente = cantidad_pendiente or 0



        if cantidad_mala > 0:

            return "M"



        if cantidad_pendiente > 0:

            return "P"



        return "B"



    def actualizar_estado_automatico(self):

        """

        El campo estado no se selecciona manualmente.



        Siempre se deriva desde las cantidades

        malas y pendientes.

        """



        self.estado = self.calcular_estado(

            self.cantidad_mala,

            self.cantidad_pendiente,

        )



    # -----------------------------------------------------

    # VALIDACIONES

    # -----------------------------------------------------



    def clean(self):

        super().clean()

        if self.lugar_id and self.tipo_de_objeto_id:
            duplicados = type(self).objects.filter(
                lugar_id=self.lugar_id, tipo_de_objeto_id=self.tipo_de_objeto_id,
            ).exclude(pk=self.pk)
            if duplicados.exists():
                raise ValidationError({
                    "tipo_de_objeto": "Esta variante ya está registrada en este lugar.",
                })



        cantidad = self.cantidad or 0

        cantidad_mala = self.cantidad_mala or 0

        cantidad_pendiente = (

            self.cantidad_pendiente or 0

        )

        minimo_operativo = (

            self.minimo_operativo if self.minimo_operativo is not None else 1

        )



        if cantidad <= 0:

            raise ValidationError({

                "cantidad":

                    "La cantidad debe ser mayor a 0."

            })



        if cantidad_mala < 0:

            raise ValidationError({

                "cantidad_mala":

                    "La cantidad mala no puede ser negativa."

            })



        if cantidad_pendiente < 0:

            raise ValidationError({

                "cantidad_pendiente":

                    "La cantidad pendiente no puede ser negativa."

            })



        if (

            cantidad_mala

            + cantidad_pendiente

            > cantidad

        ):

            raise ValidationError(

                "La suma de cantidad mala y "

                "cantidad pendiente no puede superar "

                "la cantidad total."

            )



        if minimo_operativo < 1:

            raise ValidationError({

                "minimo_operativo":

                    "El mínimo operativo debe ser "

                    "al menos 1."

            })



        if minimo_operativo > cantidad:

            raise ValidationError({

                "minimo_operativo":

                    "El mínimo operativo no puede ser "

                    "mayor que la cantidad total."

            })



    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lugar", "tipo_de_objeto"],
                name="pvsa_inventario_lugar_variante_unico",
            ),
        ]

    # -----------------------------------------------------

    # GUARDADO + HISTÓRICO AUTOMÁTICO

    # -----------------------------------------------------



    @transaction.atomic
    def save(self, *args, **kwargs):

        """

        Guarda automáticamente un histórico cuando

        cambia información relevante.



        La condición anterior se calcula utilizando

        las cantidades anteriores, evitando depender

        de posibles valores antiguos del campo estado.

        """



        anterior = None



        if self.pk:

            anterior = ObjetoLugar.objects.select_for_update().filter(

                pk=self.pk

            ).first()



        self.actualizar_estado_automatico()



        self.full_clean()



        if anterior:

            hubo_cambio = (

                anterior.cantidad

                != self.cantidad



                or

                (anterior.detalle or "")

                != (self.detalle or "")



                or

                anterior.importancia

                != self.importancia



                or

                anterior.cantidad_mala

                != self.cantidad_mala



                or

                anterior.cantidad_pendiente

                != self.cantidad_pendiente



                or

                anterior.minimo_operativo

                != self.minimo_operativo

            )



            if hubo_cambio:

                estado_anterior = (

                    self.calcular_estado(

                        anterior.cantidad_mala,

                        anterior.cantidad_pendiente,

                    )

                )



                with transaction.atomic():

                    super().save(

                        *args,

                        **kwargs,

                    )



                    HistoricoObjeto.objects.create(

                        objeto_del_lugar=self,



                        cantidad_anterior=(

                            anterior.cantidad

                        ),



                        estado_anterior=(

                            estado_anterior

                        ),



                        detalle_anterior=(

                            anterior.detalle or ""

                        ),



                        fecha_anterior=(

                            anterior.fecha

                        ),



                        importancia_anterior=(

                            anterior.importancia

                        ),



                        cantidad_mala_anterior=(

                            anterior.cantidad_mala

                        ),



                        cantidad_pendiente_anterior=(

                            anterior.cantidad_pendiente

                        ),



                        minimo_operativo_anterior=(

                            anterior.minimo_operativo

                        ),

                    )



                return



        super().save(

            *args,

            **kwargs,

        )





# =========================================================

# HISTÓRICO DE CAMBIOS

# =========================================================



class HistoricoObjeto(models.Model):



    ESTADO = ObjetoLugar.ESTADO



    importancia_anterior = (

        models.PositiveSmallIntegerField(

            default=1,

            choices=ObjetoLugar.IMPORTANCIA,

        )

    )



    cantidad_mala_anterior = (

        models.SmallIntegerField(

            default=0,

        )

    )



    cantidad_pendiente_anterior = (

        models.SmallIntegerField(

            default=0,

        )

    )



    minimo_operativo_anterior = (

        models.SmallIntegerField(

            default=1,

        )

    )



    objeto_del_lugar = models.ForeignKey(

        ObjetoLugar,

        verbose_name="objeto del lugar",

        on_delete=models.CASCADE,

        related_name="historicoobjeto",

    )



    cantidad_anterior = (

        models.SmallIntegerField()

    )



    estado_anterior = models.CharField(

        max_length=1,

        choices=ESTADO,

    )



    detalle_anterior = models.CharField(

        max_length=200,

        blank=True,

    )



    fecha_anterior = models.DateField()



    def __str__(self):

        obj = self.objeto_del_lugar



        if obj and obj.lugar:

            lugar_txt = (

                f"{obj.lugar.nombre_del_lugar} | "

                f"Piso {obj.lugar.piso.piso} | "

                f"{obj.lugar.piso.ubicacion.ubicacion}"

            )

        else:

            lugar_txt = "Sin lugar asignado"



        if (

            obj

            and obj.tipo_de_objeto

            and obj.tipo_de_objeto.objeto

        ):

            objeto_txt = (

                obj.tipo_de_objeto

                .objeto

                .nombre_del_objeto

            )



            marca_txt = (

                obj.tipo_de_objeto.marca

                or "Sin marca"

            )



            material_txt = (

                obj.tipo_de_objeto.material

                or "Sin material"

            )



        else:

            objeto_txt = "Objeto no especificado"

            marca_txt = "Sin marca"

            material_txt = "Sin material"



        return (

            f"Histórico de {objeto_txt} "

            f"- {marca_txt} {material_txt} "

            f"en {lugar_txt} "

            f"(total ant. "

            f"{self.cantidad_anterior}, "

            f"condición ant. "

            f"{self.get_estado_anterior_display()}, "

            f"fecha "

            f"{self.fecha_anterior.strftime('%d/%m/%Y')})"

        )





# =========================================================

# REGISTRO DE ACCESOS PÚBLICOS POR QR

# =========================================================





class AccesoQR(models.Model):

    """La futura vista QR creará un registro por cada consulta procesada.



    La IP y el navegador describen el origen técnico; no identifican personas.

    Este modelo no habilita el acceso público ni registra visitas por sí solo.

    """



    class Resultado(models.TextChoices):

        PERMITIDO = "permitido", "Acceso permitido"

        DESACTIVADO = "desactivado", "QR desactivado"

        INVALIDO = "invalido", "QR inválido o sustituido"



    lugar = models.ForeignKey(

        Lugar,

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name="accesos_qr",

        editable=False,

        help_text=(

            "Puede quedar vacío si el token no corresponde a un lugar "

            "o si el lugar fue eliminado."

        ),

    )



    fecha_hora = models.DateTimeField(

        auto_now_add=True,

        db_index=True,

        verbose_name="fecha y hora",

    )



    ip = models.GenericIPAddressField(

        null=True,

        blank=True,

        editable=False,

        verbose_name="dirección IP",

    )



    user_agent = models.CharField(

        max_length=512,

        blank=True,

        editable=False,

        verbose_name="navegador / dispositivo",

        help_text="La vista limitará a 512 caracteres el encabezado recibido.",

    )



    # Se guarda la huella SHA-256, no el token que permite abrir el lugar.

    # La vista normalizará los UUID antes de calcular la huella.

    # Permite correlacionar intentos sin copiar enlaces de acceso en el registro.

    token_huella = models.CharField(

        max_length=64,

        blank=True,

        db_index=True,

        editable=False,

        verbose_name="huella del token consultado",

    )



    resultado = models.CharField(

        max_length=12,

        choices=Resultado.choices,

        editable=False,

    )



    class Meta:

        ordering = ("-fecha_hora", "-pk")

        verbose_name = "acceso QR"

        verbose_name_plural = "accesos QR"



    def __str__(self):

        lugar_txt = (

            f"Lugar {self.lugar_id}"

            if self.lugar_id is not None

            else "Sin lugar asociado"

        )

        return f"{lugar_txt} | {self.get_resultado_display()}"





# =========================================================

# REPORTES DE INCIDENCIAS

# =========================================================





class ReporteIncidencia(models.Model):

    """

    Registra desperfectos comunicados mediante un QR público

    o por un usuario interno autorizado.

    """



    class Estado(models.TextChoices):

        NUEVO = "nuevo", "Nuevo"

        EN_REVISION = "en_revision", "En revisión"

        RESUELTO = "resuelto", "Resuelto"

        DESCARTADO = "descartado", "Descartado"



    class TipoProblema(models.TextChoices):

        NO_FUNCIONA = "no_funciona", "No funciona"

        FUGA = "fuga", "Fuga de agua"

        DANO = "dano", "Está dañado"

        FALTA = "falta", "Falta un elemento"

        OTRO = "otro", "Otro problema"



    class Origen(models.TextChoices):

        QR_PUBLICO = "qr_publico", "QR público"

        INTERNO = "interno", "Usuario interno"



    # Lugar donde se detectó el problema.

    lugar = models.ForeignKey(

        Lugar,

        on_delete=models.PROTECT,

        related_name="reportes_incidencias",

        verbose_name="lugar",

    )



    # Relación opcional con un objeto del inventario.

    objeto_lugar = models.ForeignKey(

        ObjetoLugar,

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name="reportes_incidencias",

        verbose_name="objeto registrado",

    )



    # Identificación del elemento reportado.

    elemento_reportado = models.CharField(

        max_length=120,

        verbose_name="elemento reportado",

    )



    tipo_problema = models.CharField(

        max_length=20,

        choices=TipoProblema.choices,

        verbose_name="tipo de problema",

    )



    # El comentario no es obligatorio.

    descripcion = models.TextField(

        max_length=1000,

        blank=True,

        verbose_name="descripción",

    )



    # La fotografía tampoco es obligatoria.



    foto = models.ImageField(

        upload_to="reportes_incidencias/%Y/%m/%d/",

        storage=EvidenciaPrivadaStorage(),

        null=True,

        blank=True,

        verbose_name="fotografía de evidencia",

    )





    origen = models.CharField(

        max_length=15,

        choices=Origen.choices,

        default=Origen.QR_PUBLICO,

        verbose_name="origen del reporte",

    )



    # Será NULL cuando reporte una persona sin cuenta.

    reportado_por = models.ForeignKey(

        settings.AUTH_USER_MODEL,

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name="incidencias_reportadas",

        verbose_name="reportado por",

    )



    # Fecha y hora automática del servidor.

    fecha_reporte = models.DateTimeField(

        auto_now_add=True,

        db_index=True,

        verbose_name="fecha y hora del reporte",

    )



    # Seguimiento de la incidencia.

    estado = models.CharField(

        max_length=20,

        choices=Estado.choices,

        default=Estado.NUEVO,

        db_index=True,

    )



    atendido_por = models.ForeignKey(

        settings.AUTH_USER_MODEL,

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name="incidencias_atendidas",

        verbose_name="atendido por",

    )



    fecha_inicio_atencion = models.DateTimeField(

        null=True,

        blank=True,

        verbose_name="inicio de atención",

    )



    fecha_resolucion = models.DateTimeField(

        null=True,

        blank=True,

        verbose_name="fecha de resolución",

    )



    observacion_resolucion = models.TextField(

        blank=True,

        verbose_name="observación de resolución",

    )



    class Meta:

        ordering = ("-fecha_reporte", "-pk")

        verbose_name = "reporte de incidencia"

        verbose_name_plural = "reportes de incidencias"



    def clean(self):

        super().clean()



        # El objeto reportado debe pertenecer al lugar indicado.

        if self.objeto_lugar_id and self.lugar_id:

            pertenece = ObjetoLugar.objects.filter(

                pk=self.objeto_lugar_id,

                lugar_id=self.lugar_id,

            ).exists()



            if not pertenece:

                raise ValidationError({

                    "objeto_lugar": (

                        "El objeto seleccionado no pertenece "

                        "al lugar reportado."

                    )

                })



    def __str__(self):

        return (

            f"Reporte #{self.pk or 'nuevo'} - "

            f"{self.elemento_reportado} - "

            f"{self.get_estado_display()}"

        )

# =========================================================
# ASIGNACIÓN DE LUGARES PROPIOS A JEFES DE DEPARTAMENTO
# =========================================================

class AsignacionLugarJefe(models.Model):
    """Lugares propios que un jefe de departamento puede administrar.

    Las áreas comunes no son lugares propios asignables. El acceso
    de consulta a áreas comunes se determinará por la ubicación
    de los lugares propios del jefe al implementar los permisos.
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lugares_asignados_como_jefe",
        verbose_name="jefe de departamento",
    )

    lugar = models.ForeignKey(
        Lugar,
        on_delete=models.CASCADE,
        related_name="asignaciones_jefes",
        verbose_name="lugar propio asignado",
    )

    asignado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asignaciones_jefes_realizadas",
        verbose_name="asignado por",
    )

    fecha_asignacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="fecha y hora de asignación",
    )

    class Meta:
        verbose_name = "asignación de lugar a jefe"
        verbose_name_plural = "asignaciones de lugares a jefes"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "lugar"],
                name="pvsa_jefe_lugar_unico",
            ),
        ]

    def clean(self):
        super().clean()
        if self.lugar_id and Lugar.objects.filter(
            pk=self.lugar_id,
            es_area_comun=True,
        ).exists():
            raise ValidationError({
                "lugar": (
                    "Las áreas comunes no se asignan como espacios "
                    "propios de un jefe de departamento."
                ),
            })

    def __str__(self):
        return (
            f"{self.usuario.get_username()} - "
            f"{self.lugar.nombre_del_lugar}"
        )


# =========================================================
# AUDITORÍA DE CAMBIOS DE INVENTARIO HECHOS POR JEFES
# =========================================================

class AuditoriaInventarioJefe(models.Model):
    """Evidencia de quién creó/editó un objeto, cuándo y qué cambió.

    Conserva los IDs y el nombre del actor incluso si el lugar,
    objeto o cuenta cambian o desaparecen posteriormente.
    La escritura se hace dentro de la misma transacción del inventario.
    """

    class Accion(models.TextChoices):
        CREAR = "crear", "Creación de objeto"
        EDITAR = "editar", "Edición de objeto"

    accion = models.CharField(
        max_length=10,
        choices=Accion.choices,
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias_inventario_como_jefe",
        editable=False,
    )
    usuario_nombre = models.CharField(max_length=150, editable=False)
    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True)
    lugar_id_registrado = models.PositiveBigIntegerField(editable=False)
    objeto_lugar_id_registrado = models.PositiveBigIntegerField(editable=False)
    datos_antes = models.JSONField(default=dict, editable=False)
    datos_despues = models.JSONField(default=dict, editable=False)

    class Meta:
        ordering = ("-fecha_hora", "-id")
        verbose_name = "auditoría de inventario de jefe"
        verbose_name_plural = "auditorías de inventario de jefes"

    def __str__(self):
        return (
            f"{self.get_accion_display()} | {self.usuario_nombre} | "
            f"Objeto #{self.objeto_lugar_id_registrado} | {self.fecha_hora}"
        )
