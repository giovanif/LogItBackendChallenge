# Generated by Django 4.0.6 on 2022-07-27 21:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0005_hand_hand_stopped'),
    ]

    operations = [
        migrations.AddField(
            model_name='hand',
            name='hand_points',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]