from django.core.exceptions import ValidationError
from django.db import models, transaction

from .estructura import Lugar
from .catalogos import TipoObjeto


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

    @property

    def cantidad_buena(self):

        cantidad = self.cantidad or 0

        malas = self.cantidad_mala or 0

        pendientes = self.cantidad_pendiente or 0

        buenas = cantidad - malas - pendientes

        return max(buenas, 0)

    @property

    def unidades_funcionales_equivalentes(self):

        cantidad = self.cantidad or 0

        malas = self.cantidad_mala or 0

        pendientes = self.cantidad_pendiente or 0

        equivalentes = (

            cantidad

            - malas

            - (pendientes * 0.5)

        )

        return max(equivalentes, 0)

    @property

    def operatividad_objeto(self):

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

    @staticmethod

    def calcular_estado(

        cantidad_mala,

        cantidad_pendiente,

    ):

        cantidad_mala = cantidad_mala or 0

        cantidad_pendiente = cantidad_pendiente or 0

        if cantidad_mala > 0:

            return "M"

        if cantidad_pendiente > 0:

            return "P"

        return "B"

    def actualizar_estado_automatico(self):

        self.estado = self.calcular_estado(

            self.cantidad_mala,

            self.cantidad_pendiente,

        )

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

    @transaction.atomic
    def save(self, *args, **kwargs):

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
