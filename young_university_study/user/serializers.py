from rest_framework import serializers
from .models import *
import json
import requests


class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        model = College
        fields = '__all__'
        read_only_fields = ('id',)


class CollegeRanksResponseSerializer(serializers.ModelSerializer):
    total_study = serializers.IntegerField()

    class Meta:
        model = College
        fields = '__all__'
        read_only_fields = ('id',)


class CollegeRankRequestSerializer(serializers.Serializer):
    college_id = serializers.IntegerField()


class LeagueBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeagueBranch
        fields = '__all__'
        read_only_fields = ('id',)


class LeagueBranchRanksResponseSerializer(serializers.ModelSerializer):
    total_study = serializers.IntegerField()

    class Meta:
        model = LeagueBranch
        fields = '__all__'
        read_only_fields = ('id',)


class LeagueBranchRankRequestSerializer(serializers.Serializer):
    college_id = serializers.IntegerField()
    league_branch_id = serializers.IntegerField()


class PermissionSerializer(serializers.ModelSerializer):
    permission_name = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Permission
        fields = ['id', 'user_id', 'permission_type',
                  'permission_id', 'permission_name']


class UserSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(read_only=True, many=True)
    college = CollegeSerializer()
    league_branch = LeagueBranchSerializer()

    class Meta:
        model = User
        exclude = ( 'password', 'is_staff', 'is_active',
                   'user_permissions', 'groups')


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['college', 'league_branch']


class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['code']

    def validate_code(self, value):
        """
        检查code
        """
        try:
            r = requests.get(
                'https://youth.bupt.edu.cn/token/wx_info?code=' +  value)
            data = r.json()
            return data['openid']
        except Exception as e:
            raise serializers.ValidationError("请输入正确code")



class UserRankResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        read_only_fields = ('last_login', 'modified', 'created',
                            'continue_study', 'id', 'name', 'total_study', 'total_score')
        exclude = ('code', 'password', 'is_staff', 'is_active',
                   'user_permissions', 'is_superuser', 'groups', 'college', 'league_branch')


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'college', 'league_branch', 'identity', 'uid', 'code']

    def validate_code(self, value):
        """
        检查code
        """
        try:
            r = requests.get(
                'https://youth.bupt.edu.cn/token/wx_info?code=' +  value)
            data = r.json()
            return data['openid']
        except Exception as e:
            raise serializers.ValidationError("请输入正确code")

    def validate_uid(self, value):
        """
        检查uid
        """
        r = requests.get(
            "http://app.bjtitle.com/rui/bj-band.php?u=%d&t=1" % value)

        if r.text == "参数错误":
            raise serializers.ValidationError("请正确输入uid")
        return value


class RankResponseSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    total = serializers.IntegerField()
