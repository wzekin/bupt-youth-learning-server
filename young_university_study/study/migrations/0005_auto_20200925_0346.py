# Generated by Django 3.1 on 2020-09-25 03:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('study', '0004_auto_20200824_0855'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studyrecording',
            name='user_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recording', to=settings.AUTH_USER_MODEL),
        ),
    ]
