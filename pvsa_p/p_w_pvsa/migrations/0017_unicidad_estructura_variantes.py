from django.db import migrations, models

from p_w_pvsa.modelos.estructura import ClaveNormalizada


def comprobar_duplicados(apps, schema_editor):
    def clave(valor):
        return " ".join((valor or "").split()).casefold()

    alias = schema_editor.connection.alias
    configuraciones = (
        ("Piso", ("ubicacion_id", "piso"), lambda fila: fila),
        ("Lugar", ("piso_id", "nombre_del_lugar"), lambda fila: (fila[0], clave(fila[1]))),
        ("TipoObjeto", ("objeto_id", "marca", "material"), lambda fila: (fila[0], clave(fila[1]), clave(fila[2]))),
    )
    for nombre, campos, normalizar in configuraciones:
        vistos = {}
        modelo = apps.get_model("p_w_pvsa", nombre)
        for fila in modelo.objects.using(alias).order_by("pk").values_list("pk", *campos).iterator():
            firma = normalizar(fila[1:])
            if firma in vistos:
                raise RuntimeError(
                    f"No se puede activar la unicidad de {nombre}: registros equivalentes {vistos[firma]} y {fila[0]}. "
                    "No se modificaron datos. Requiere revisión manual, sin fusionar ni eliminar automáticamente."
                )
            vistos[firma] = fila[0]


class Migration(migrations.Migration):
    dependencies = [("p_w_pvsa", "0016_alter_accesoqr_resultado")]

    operations = [
        migrations.RunPython(comprobar_duplicados, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="piso",
            constraint=models.UniqueConstraint(fields=("ubicacion", "piso"), name="pvsa_piso_ubicacion_unico"),
        ),
        migrations.AddConstraint(
            model_name="lugar",
            constraint=models.UniqueConstraint(models.F("piso"), ClaveNormalizada("nombre_del_lugar"), name="pvsa_lugar_piso_nombre_unico"),
        ),
        migrations.AddConstraint(
            model_name="tipoobjeto",
            constraint=models.UniqueConstraint(models.F("objeto"), ClaveNormalizada("marca"), ClaveNormalizada("material"), name="pvsa_variante_objeto_unica"),
        ),
    ]
