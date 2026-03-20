from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='country',
            field=models.CharField(
                choices=[('NG', 'Nigeria'), ('GH', 'Ghana')],
                default='NG',
                max_length=2,
            ),
        ),
    ]
