# Generated by Django 3.1 on 2020-08-24 02:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_auto_20200823_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='total_score',
            field=models.IntegerField(default=0, verbose_name='总积分'),
        ),
    ]
