# Generated by Django 5.0.3 on 2024-03-25 20:38

import user.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="avatar",
            field=models.ImageField(
                null=True, upload_to=user.models.user_image_file_path
            ),
        ),
    ]
