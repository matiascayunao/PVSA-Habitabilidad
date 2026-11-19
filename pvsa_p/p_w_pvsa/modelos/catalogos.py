from django.core.exceptions import ValidationError
from django.db import models

from .estructura import TipoLugar, ClaveNormalizada, clave_normalizada


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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                models.F("objeto"), ClaveNormalizada("marca"), ClaveNormalizada("material"),
                name="pvsa_variante_objeto_unica",
            ),
        ]

    def clean(self):
        super().clean()
        if self.objeto_id and type(self).objects.annotate(
            _marca=ClaveNormalizada("marca"), _material=ClaveNormalizada("material"),
        ).filter(
            objeto_id=self.objeto_id, _marca=clave_normalizada(self.marca),
            _material=clave_normalizada(self.material),
        ).exclude(pk=self.pk).exists():
            raise ValidationError("Esta variante ya existe para el objeto seleccionado.")

    @property
    def etiqueta_atributos(self):
        marca = (self.marca or "").strip()
        material = (self.material or "").strip()
        detalles = f"{marca or 'Sin marca'} · {material or 'Sin material'}"
        if not marca and not material:
            estado = "Atributos vacíos"
        elif not marca or not material:
            estado = "Atributos parcialmente vacíos"
        else:
            estado = "Texto registrado"
        identidad = f" (ID {self.pk})" if self.pk is not None else ""
        return f"{detalles} — {estado}{identidad}"

    def __str__(self):
        return f"{self.objeto.nombre_del_objeto} - {self.etiqueta_atributos}"


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
