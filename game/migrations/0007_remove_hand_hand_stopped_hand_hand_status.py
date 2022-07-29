# Generated by Django 4.0.6 on 2022-07-28 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0006_hand_hand_points'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='hand',
            name='hand_stopped',
        ),
        migrations.AddField(
            model_name='hand',
            name='hand_status',
            field=models.CharField(default=1, max_length=15),
            preserve_default=False,
        ),
    ]
