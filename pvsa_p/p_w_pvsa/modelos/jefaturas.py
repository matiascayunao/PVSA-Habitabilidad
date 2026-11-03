from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .estructura import Lugar


class AsignacionLugarJefe(models.Model):

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


class AuditoriaInventarioJefe(models.Model):

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
