# Generated by Django 3.1.7 on 2021-03-06 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_commodity_deadline'),
    ]

    operations = [
        migrations.AddField(
            model_name='commodity',
            name='location',
            field=models.CharField(default='null', max_length=50, verbose_name='兑换地点'),
            preserve_default=False,
        ),
    ]