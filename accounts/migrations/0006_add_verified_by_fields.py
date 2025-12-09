from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_alter_request_payment_receipt'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='requirements_verified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requirements_verified_requests', to='accounts.adminaccount'),
        ),
        migrations.AddField(
            model_name='request',
            name='payment_verified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_verified_requests', to='accounts.adminaccount'),
        ),
        migrations.AddField(
            model_name='request',
            name='completed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='completed_requests', to='accounts.adminaccount'),
        ),
    ]
