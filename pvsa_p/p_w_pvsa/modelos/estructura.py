import uuid

from django.db import models


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

    qr_token = models.UUIDField(

        default=uuid.uuid4,

        unique=True,

        editable=False,

        verbose_name="token QR",

    )

    qr_activo = models.BooleanField(

        default=False,

        editable=False,

        verbose_name="QR activo",

    )

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

        if self._state.adding:

            if self.es_area_comun:

                self.visibilidad_qr = "publico"

            else:

                self.visibilidad_qr = "privado"

            self.qr_activo = True

        super().save(*args, **kwargs)

    def __str__(self):

        return (

            f"{self.nombre_del_lugar} | "

            f"Piso {self.piso.piso} | "

            f"{self.piso.ubicacion.ubicacion}"

        )

    @property

    def operatividad_lugar(self):

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
