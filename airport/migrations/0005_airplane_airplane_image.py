# Generated by Django 5.0.3 on 2024-03-25 19:19

import airport.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("airport", "0004_remove_airport_closest_big_city_alter_airport_city_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="airplane",
            name="airplane_image",
            field=models.ImageField(
                null=True, upload_to=airport.models.airplane_image_file_path
            ),
        ),
    ]
