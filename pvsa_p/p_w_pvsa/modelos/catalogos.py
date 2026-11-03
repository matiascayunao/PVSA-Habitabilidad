from django.db import models

from .estructura import TipoLugar


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
