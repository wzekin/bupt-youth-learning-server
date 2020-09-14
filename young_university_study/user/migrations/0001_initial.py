# Generated by Django 3.1 on 2020-08-23 11:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import young_university_study.user.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='College',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=20, verbose_name='学院')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='LeagueBranch',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=20, verbose_name='团支部')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('college', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='user.college', verbose_name='学院')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('id', models.IntegerField(primary_key=True, serialize=False, verbose_name='学号')),
                ('name', models.CharField(max_length=20, verbose_name='姓名')),
                ('is_superuser', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('openid', models.CharField(max_length=100, null=True, unique=True, verbose_name='微信openid')),
                ('continue_study', models.IntegerField(default=0, verbose_name='连续学习期数')),
                ('modified', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('college', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='user.college', verbose_name='学院')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('league_branch', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='user.leaguebranch', verbose_name='团支部')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
            managers=[
                ('objects', young_university_study.user.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission_id', models.IntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('permission_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='type', to='contenttypes.contenttype')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permissions', to=settings.AUTH_USER_MODEL, verbose_name='学号')),
            ],
            options={
                'unique_together': {('user_id', 'permission_type', 'permission_id')},
            },
        ),
    ]
