from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_user_bank_account_name_user_bank_account_number_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='kyc_rejection_reason',
            field=models.TextField(blank=True, null=True),
        ),
    ]
