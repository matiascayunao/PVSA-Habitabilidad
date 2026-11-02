"""Fail closed on existing duplicates; never merge/delete operational data."""
from django.db import migrations, models
from django.db.models import Count


def comprobar_duplicados(apps, schema_editor):
    Inventario = apps.get_model("p_w_pvsa", "ObjetoLugar")
    duplicados = list(
        Inventario.objects.using(schema_editor.connection.alias)
        .exclude(lugar_id=None).exclude(tipo_de_objeto_id=None)
        .values("lugar_id", "tipo_de_objeto_id")
        .annotate(total=Count("pk")).filter(total__gt=1)[:10]
    )
    if duplicados:
        raise RuntimeError(
            "No se puede activar la unicidad del inventario. "
            "Revise manualmente los grupos duplicados (sin fusionar ni borrar "
            f"históricos automáticamente): {duplicados}"
        )


class Migration(migrations.Migration):
    dependencies = [("p_w_pvsa", "0014_auditoriainventariojefe")]
    operations = [
        migrations.RunPython(comprobar_duplicados, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="objetolugar",
            constraint=models.UniqueConstraint(
                fields=("lugar", "tipo_de_objeto"),
                name="pvsa_inventario_lugar_variante_unico",
            ),
        ),
    ]
