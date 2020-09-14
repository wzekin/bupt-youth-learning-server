# Generated by Django 3.1 on 2020-08-25 06:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_auto_20200824_0855'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='openid',
        ),
        migrations.AddField(
            model_name='user',
            name='code',
            field=models.CharField(default='', max_length=100, unique=True, verbose_name='微信openid'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='identity',
            field=models.SmallIntegerField(choices=[(1, '团员'), (2, '干部'), (3, '青年')], default=1, verbose_name='学生身份'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='uid',
            field=models.IntegerField(default=11, unique=True, verbose_name='某个uid'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='user',
            name='college',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='user.college', verbose_name='学院'),
        ),
        migrations.AlterField(
            model_name='user',
            name='league_branch',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='user.leaguebranch', verbose_name='团支部'),
        ),
    ]
