from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from ..private_storage import EvidenciaPrivadaStorage
from .estructura import Lugar
from .inventario import ObjetoLugar


class AccesoQR(models.Model):

    class Resultado(models.TextChoices):

        PERMITIDO = "permitido", "Acceso permitido"

        DESACTIVADO = "desactivado", "QR desactivado"

        INVALIDO = "invalido", "QR inválido o sustituido"

        DENEGADO = "denegado", "Acceso denegado"

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


class ReporteIncidencia(models.Model):

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

    lugar = models.ForeignKey(

        Lugar,

        on_delete=models.PROTECT,

        related_name="reportes_incidencias",

        verbose_name="lugar",

    )

    objeto_lugar = models.ForeignKey(

        ObjetoLugar,

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name="reportes_incidencias",

        verbose_name="objeto registrado",

    )

    elemento_reportado = models.CharField(

        max_length=120,

        verbose_name="elemento reportado",

    )

    tipo_problema = models.CharField(

        max_length=20,

        choices=TipoProblema.choices,

        verbose_name="tipo de problema",

    )

    descripcion = models.TextField(

        max_length=1000,

        blank=True,

        verbose_name="descripción",

    )

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

    reportado_por = models.ForeignKey(

        settings.AUTH_USER_MODEL,

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name="incidencias_reportadas",

        verbose_name="reportado por",

    )

    fecha_reporte = models.DateTimeField(

        auto_now_add=True,

        db_index=True,

        verbose_name="fecha y hora del reporte",

    )

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
