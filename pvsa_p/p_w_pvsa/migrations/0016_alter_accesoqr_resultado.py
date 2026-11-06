from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("p_w_pvsa", "0015_inventario_lugar_variante_unico")]

    operations = [
        migrations.AlterField(
            model_name="accesoqr",
            name="resultado",
            field=models.CharField(
                choices=[
                    ("permitido", "Acceso permitido"),
                    ("desactivado", "QR desactivado"),
                    ("invalido", "QR inv\u00e1lido o sustituido"),
                    ("denegado", "Acceso denegado"),
                ],
                editable=False,
                max_length=12,
            ),
        ),
    ]
