from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='country',
            field=models.CharField(
                choices=[('NG', 'Nigeria'), ('GH', 'Ghana')],
                default='NG',
                max_length=2,
            ),
        ),
    ]
