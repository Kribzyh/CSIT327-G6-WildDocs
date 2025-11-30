from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_studentaccount_profile_picture"),
    ]

    operations = [
        migrations.AddField(
            model_name="request",
            name="completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="request",
            name="payment_feedback",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="request",
            name="payment_receipt",
            field=models.FileField(blank=True, null=True, upload_to="payment_receipts/"),
        ),
        migrations.AddField(
            model_name="request",
            name="payment_reference_code",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="request",
            name="payment_submitted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="request",
            name="payment_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="request",
            name="ready_for_pickup_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="request",
            name="requirements_feedback",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="request",
            name="requirements_instructions",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="request",
            name="requirements_submission_file",
            field=models.FileField(blank=True, null=True, upload_to="requirements_submissions/"),
        ),
        migrations.AddField(
            model_name="request",
            name="requirements_submission_note",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="request",
            name="requirements_submitted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="request",
            name="requirements_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
