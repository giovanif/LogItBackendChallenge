# Generated by Django 4.0.6 on 2022-07-26 19:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='match',
            old_name='game_id',
            new_name='match_id',
        ),
    ]
