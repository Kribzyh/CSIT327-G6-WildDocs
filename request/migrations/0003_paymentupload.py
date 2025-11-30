from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_studentaccount_profile_picture'),
        ('request', '0002_requirementupload'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_name', models.CharField(max_length=512)),
                ('file_url', models.TextField(blank=True)),
                ('supabase_id', models.CharField(blank=True, max_length=255, null=True)),
                ('delete_url', models.TextField(blank=True)),
                ('content_type', models.CharField(blank=True, max_length=100, null=True)),
                ('file_size', models.BigIntegerField(blank=True, null=True)),
                ('provider', models.CharField(default='supabase', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_uploads', to='accounts.request')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_uploads', to='accounts.studentaccount')),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Payment Upload',
                'verbose_name_plural': 'Payment Uploads',
            },
        ),
    ]
