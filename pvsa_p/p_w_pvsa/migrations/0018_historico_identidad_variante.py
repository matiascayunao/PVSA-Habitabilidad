from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("p_w_pvsa", "0017_unicidad_estructura_variantes")]

    operations = [
        migrations.AddField(
            model_name="historicoobjeto",
            name="variante_anterior",
            field=models.JSONField(blank=True, editable=False, null=True),
        ),
        migrations.RunSQL(
            sql="""
                CREATE TRIGGER pvsa_historico_variante_inmutable
                BEFORE UPDATE OF variante_anterior ON p_w_pvsa_historicoobjeto
                WHEN OLD.variante_anterior IS NOT NEW.variante_anterior
                BEGIN
                    SELECT RAISE(ABORT, 'La identidad de la variante histórica es inmutable.');
                END
            """,
            reverse_sql="DROP TRIGGER pvsa_historico_variante_inmutable",
        ),
    ]
