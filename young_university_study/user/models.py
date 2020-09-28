from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Create your models here.


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, name, password, **extra_fields):
        values = [name]
        field_value_map = dict(zip(self.model.REQUIRED_FIELDS, values))
        for field_name, value in field_value_map.items():
            if not value:
                raise ValueError('The {} value must be set'.format(field_name))

        user = self.model(
            name=name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, name, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('identity', 3)
        return self._create_user(name, password, **extra_fields)

    def create_superuser(self, name, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('identity', 2)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        return self._create_user(name, password, **extra_fields)


class College(models.Model):
    """
      学院表 
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField("学院", max_length=20, null=False)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class LeagueBranch(models.Model):
    """
      团支部表
    """
    id = models.AutoField(primary_key=True)
    college = models.ForeignKey(College,
                                verbose_name="学院", null=False, db_index=True, on_delete=models.PROTECT)
    name = models.CharField("团支部", max_length=20, null=False)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s-%s' % (self.college.name, self.name)

    class Meta:
        unique_together = (("name", "college"),)


class User(AbstractBaseUser, PermissionsMixin):
    """
      用户表
    """

    id = models.IntegerField("学号", primary_key=True)
    name = models.CharField("姓名", max_length=20, null=False)
    college = models.ForeignKey(
        College, verbose_name="学院", null=True, db_index=True, on_delete=models.SET_NULL)
    league_branch = models.ForeignKey(
        LeagueBranch,  verbose_name="团支部", null=True, db_index=True, on_delete=models.SET_NULL)

    IDENTITY_CHOICES = [(1, '团员'), (2, '干部'), (3, '青年')]
    identity = models.SmallIntegerField(
        "学生身份", null=False, choices=IDENTITY_CHOICES)

    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    code = models.CharField("微信openid",
                            max_length=100, null=False, unique=True)
    uid = models.IntegerField("某个uid", null=False, unique=True)

    continue_study = models.IntegerField("连续学习期数", default=0)
    total_study = models.IntegerField("总学习期数", default=0)
    total_score = models.IntegerField("总积分", default=0)

    USERNAME_FIELD = "id"
    REQUIRED_FIELDS = ['name', 'code', 'uid']

    objects = UserManager()

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def __str__(self):
        return str(self.id)

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)


class Permission(models.Model):
    user_id = models.ForeignKey(User, related_name='permissions',
                                verbose_name="学号", null=False, on_delete=models.CASCADE)
    permission_type = models.ForeignKey(
        ContentType, related_name='type', on_delete=models.CASCADE)
    permission_id = models.IntegerField()
    permission_name = GenericForeignKey('permission_type', 'permission_id')

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user_id", "permission_type", "permission_id"),)


def user_has_college_permission(user, college_id):
    if user.is_anonymous:
        return False
    return user.is_superuser or user.permissions.filter(permission_type=ContentType.objects.get_for_model(College), permission_id=college_id).exists()


def user_has_league_permission(user, college_id, league_id):
    if user.is_anonymous:
        return False
    return (
        user.is_superuser or
            user.permissions.filter(permission_type=ContentType.objects.get_for_model(LeagueBranch), permission_id=league_id).exists()
                or (
                    user_has_college_permission(user, college_id)
                    and LeagueBranch.objects.filter(id=league_id, college=college_id).exists()
                )
            )
