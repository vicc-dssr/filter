# Generated by Django 3.1.7 on 2021-04-02 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('filterapp', '0002_init_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='batch_cnt',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='game',
            name='k_factor',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
