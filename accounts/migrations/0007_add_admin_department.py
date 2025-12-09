from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_add_verified_by_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='adminaccount',
            name='department',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
