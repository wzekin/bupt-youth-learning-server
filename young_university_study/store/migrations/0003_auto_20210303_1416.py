# Generated by Django 3.1.7 on 2021-03-03 14:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_auto_20210226_1319'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commodity',
            name='picture',
            field=models.CharField(max_length=100, null=True, verbose_name='商品图片'),
        ),
    ]