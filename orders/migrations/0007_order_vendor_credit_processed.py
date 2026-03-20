from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_payoutrequest_paid_at_payoutrequest_processed_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='vendor_credit_processed',
            field=models.BooleanField(default=False),
        ),
    ]
