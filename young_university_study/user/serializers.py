import requests
from rest_framework import serializers

from ..study.models import get_recording_num
from .models import College, LeagueBranch, Permission, User


class CodeMixin:
    def validate_code(self, value):
        """
        检查code
        """
        try:
            r = requests.get(
                'https://youth.bupt.edu.cn/token/wx_info?code=' + value)
            data = r.json()
            return data['openid']
        except Exception as e:
            raise serializers.ValidationError("请输入正确code")


class CollegeSerializer(serializers.ModelSerializer):
    """
    CollegeSerializer 基础College序列化类
    """
    class Meta:
        model = College
        fields = '__all__'
        read_only_fields = ('id',)


class LeagueBranchSerializer(serializers.ModelSerializer):

    """
    LeagueBranchSerializer 基础LeagueBranch序列化类
    """
    class Meta:
        model = LeagueBranch
        fields = '__all__'
        read_only_fields = ('id',)


class PermissionSerializer(serializers.ModelSerializer):
    """
    PermissionSerializer 基础Permission序列化类
    """
    permission_name = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Permission
        fields = ['id', 'user_id', 'permission_type',
                  'permission_id', 'permission_name']


class UserSerializer(serializers.ModelSerializer):
    """
    UserSerializer 基础User序列化类
    """
    permissions = PermissionSerializer(read_only=True, many=True)
    college = CollegeSerializer()
    league_branch = LeagueBranchSerializer()

    class Meta:
        model = User
        exclude = ('password', 'is_staff', 'is_active',
                   'user_permissions', 'groups')


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    UserUpdateSerializer 用户更新请求
    """
    class Meta:
        model = User
        fields = ['college', 'league_branch']

    def validate(self, data):
        college = data['college']
        league_branch = data['league_branch']
        if not LeagueBranch.objects.filter(id=league_branch.id, college=college).exists():
            raise serializers.ValidationError("学院中没有此团支部")
        return data


class UserLoginSerializer(serializers.ModelSerializer, CodeMixin):
    class Meta:
        model = User
        fields = ['code']


class UserCreateSerializer(serializers.ModelSerializer, CodeMixin):
    class Meta:
        model = User
        fields = ['id', 'name', 'college',
                  'league_branch', 'identity', 'uid', 'code']

    def validate_id(self, value):
        """
        检查id是否重复
        """
        if User.objects.filter(id=value).exists():
            raise serializers.ValidationError("该用户已经存在！")
        return value

    def validate_uid(self, value):
        """
        检查uid
        """
        r = requests.get(
            "http://app.bjtitle.com/rui/bj-band.php?u=%d&t=1" % value)

        if r.text == "参数错误":
            raise serializers.ValidationError("请正确输入uid")
        return value


class CollegeRequestSerializer(serializers.Serializer):
    """
    College请求，获取单个College或者College下的所有团支部
    """
    college_id = serializers.IntegerField()


class LeagueBranchRequestSerializer(serializers.Serializer):

    """
    LeagueBranch请求，获取单个LeagueBranch或者LeagueBranch下的所有学生
    """
    college_id = serializers.IntegerField()
    league_branch_id = serializers.IntegerField()


class RanksMixin(serializers.Serializer):
    """
    RanksMixin

    for ranks api
    加入total_study字段，表示所有学习数量
    """
    total_study = serializers.IntegerField()


class CollegeRanksResponseSerializer(CollegeSerializer, RanksMixin):
    """
    CollegeRanksResponseSerializer

    继承自CollegeSerializer, 加入了total_study字段
    """
    pass


class LeagueBranchRanksResponseSerializer(LeagueBranchSerializer, RanksMixin):
    """
    LeagueBranchRanksResponseSerializer

    继承自LeagueBranchSerializer，加入total_study字段
    """
    pass


class RankResponseSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    total = serializers.IntegerField()


class RankInRangeMixin(serializers.Serializer):
    """
    RankInRange 请求，Mixin类
    每个RankInRange都会有study_min和study_max的参数
    """
    study_min = serializers.IntegerField()
    study_max = serializers.IntegerField()


class CollegeRankInRangeRequestSerializer(RankInRangeMixin):
    pass


class LeagueRankInRangeRequestSerializer(RankInRangeMixin, CollegeRequestSerializer):
    pass


class UserRankInRangeRequestSerializer(RankInRangeMixin, LeagueBranchRequestSerializer):
    pass


class RankInRangeResponseSerializer(serializers.ModelSerializer):
    """
    RankInRange返回, 加入total_study_in_range和finish_rate
    """
    total_study_in_range = serializers.IntegerField()
    finish_rate = serializers.FloatField()
    user_num = serializers.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        study_min = kwargs.pop('study_min', None)
        study_max = kwargs.pop('study_max', None)
        self.recording_num = get_recording_num(study_min, study_max)

        # Instantiate the superclass normally
        super(RankInRangeResponseSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, instance):
        """Convert `username` to lowercase."""
        user_num = instance.user_num if hasattr(instance, 'user_num') else 1
        recording_num = self.recording_num * user_num
        if recording_num != 0:
            instance.finish_rate = instance.total_study_in_range / recording_num
        else:
            instance.finish_rate = 0
        return super().to_representation(instance)


class UserRankInRangeResponseSerializer(RankInRangeResponseSerializer):
    class Meta:
        model = User
        exclude = ('password', 'is_staff', 'is_active',
                   'user_permissions', 'groups')


class LeagueRankInRangeResponseSerializer(RankInRangeResponseSerializer, LeagueBranchSerializer):
    pass


class CollegeRankInRangeResponseSerializer(RankInRangeResponseSerializer, CollegeSerializer):
    pass
