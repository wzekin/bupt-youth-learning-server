# Generated by Django 3.1.7 on 2021-03-05 15:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_auto_20200925_0346'),
        ('store', '0004_commodity_is_removed'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaserecord',
            name='is_exchanged',
            field=models.BooleanField(default=False, verbose_name='是否已经兑换'),
        ),
        migrations.AlterField(
            model_name='commodity',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user.college'),
        ),
    ]
