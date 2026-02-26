from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_payoutrequest'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='payoutrequest',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payoutrequest',
            name='processed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_payouts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='payoutrequest',
            name='transfer_reference',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
    ]
