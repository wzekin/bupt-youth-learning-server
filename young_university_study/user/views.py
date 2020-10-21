from django.contrib.auth import login
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.status import HTTP_200_OK

from .models import (College, LeagueBranch, Permission, User,
                     user_has_college_permission, user_has_league_permission)
from .serializers import (CollegeRankInRangeRequestSerializer,
                          CollegeRankInRangeResponseSerializer,
                          CollegeRanksResponseSerializer,
                          CollegeRequestSerializer, CollegeSerializer,
                          LeagueBranchRanksResponseSerializer,
                          LeagueBranchRequestSerializer,
                          LeagueBranchSerializer,
                          LeagueRankInRangeRequestSerializer,
                          LeagueRankInRangeResponseSerializer,
                          PermissionSerializer, RankResponseSerializer,
                          UserCreateSerializer, UserLoginSerializer,
                          UserRankInRangeRequestSerializer,
                          UserRankInRangeResponseSerializer, UserSerializer,
                          UserUpdateSerializer)


class BaseViewSet(viewsets.GenericViewSet):
    serializer_class_map = {}

    def get_serializer_class(self):
        if self.action in self.serializer_class_map:
            return self.serializer_class_map[self.action]
        else:
            return super().get_serializer_class()


class UserViewSetPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # 只有校级管理员可以创建
        if view.action == 'rank' and request.user.is_anonymous:
            return False
        if view.action == 'list':
            return request.user.is_superuser
        return True

    def has_object_permission(self, request, view, obj):
        # 只有校级管理员可以删除
        return user_has_league_permission(request.user, obj.college_id, obj.league_branch_id)


class UserViewSet(
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        mixins.CreateModelMixin,
        BaseViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (UserViewSetPermission,)
    serializer_class_map = {
        'me': UserUpdateSerializer,
        'update': UserUpdateSerializer,
        'create': UserCreateSerializer,
        'login': UserLoginSerializer,
    }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        login(request, serializer.instance)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=['POST'], detail=False)
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(code=serializer.data['code'])
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)
        return Response("", status=status.HTTP_200_OK)

    @action(methods=['GET', 'PUT'], detail=False)
    def me(self, request):
        u = self.request.user
        if u.is_anonymous:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if request.method == 'GET':
            serializer = UserSerializer(u)
            return Response(serializer.data)
        if request.method == 'PUT':
            serializer = self.get_serializer(
                u, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            if getattr(u, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                u._prefetched_objects_cache = {}

            return Response(serializer.data)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        college = serializer.validated_data['college']
        league = serializer.validated_data['league_branch']

        if instance.college_id != college.id:
            if not user_has_college_permission(request.user, instance.college_id):
                return Response(status=status.HTTP_403_FORBIDDEN)

        instance.college_id = college.id
        instance.league_branch_id = league.id

        instance.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def search(self, request):
        name = self.request.query_params.get('name', None)
        if name is None:
            return Response(status.HTTP_400_BAD_REQUEST)

        users = User.objects.all()
        if not self.request.user.is_superuser:
            QQ = Q(id=0)
            for p in self.request.user.permissions:
                if p.permission_type == ContentType.objects.get_for_model(College):
                    QQ = QQ | Q(college=p.permission_id)
                elif p.permission_type == ContentType.objects.get_for_model(LeagueBranch):
                    QQ = QQ | Q(leagur_branch=p.permission_id)

            users = users.filter(QQ)

        users = users.filter(name=name).select_related("college").select_related(
            "league_branch").prefetch_related("permissions")
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(operation_description='获得当前学生的排名，以及学生总人数',
                         responses={200: RankResponseSerializer()})
    def rank(self, request):
        rank = User.objects.filter(
            total_study__gt=request.user.total_study).count() + 1  # 计算为前面有多少人，所以+1
        total = User.objects.all().count()
        return Response({'rank': rank, 'total': total}, status=HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(operation_description='获得团支部的所有学生的信息',
                         query_serializer=LeagueBranchRequestSerializer,
                         responses={200: UserSerializer(many=True)})
    def ranks(self, request):
        serializer = LeagueBranchRequestSerializer(
            data=request.query_params)
        serializer.is_valid(raise_exception=True)

        u = request.user
        college_id = serializer.validated_data['college_id']
        league_branch_id = serializer.validated_data['league_branch_id']

        if not user_has_league_permission(u, college_id, league_branch_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        queryset = User.objects.filter(
            college=college_id, league_branch=league_branch_id).select_related("college").select_related("league_branch").prefetch_related("permissions")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(operation_description='获得团支部的所有学生的信息',
                         query_serializer=UserRankInRangeRequestSerializer,
                         responses={200: UserSerializer(many=True)})
    def ranks_in_range(self, request):
        serializer = UserRankInRangeRequestSerializer(
            data=request.query_params)
        serializer.is_valid(raise_exception=True)

        u = request.user
        college_id = serializer.validated_data['college_id']
        league_branch_id = serializer.validated_data['league_branch_id']
        study_min = serializer.validated_data['study_min']
        study_max = serializer.validated_data['study_max']

        if not user_has_league_permission(u, college_id, league_branch_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        queryset = User.objects.filter(
            college=college_id, league_branch=league_branch_id
        ).select_related("college").select_related("league_branch").annotate(
            total_study_in_range=models.Count("recording__id", distinct=True, filter=models.Q(
                recording__study_id__gte=study_min, recording__study_id__lte=study_max))
        ).order_by('-total_study_in_range')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserRankInRangeResponseSerializer(
                page, many=True, study_min=study_min, study_max=study_max)
            return self.get_paginated_response(serializer.data)

        serializer = UserRankInRangeResponseSerializer(
            queryset, many=True, study_min=study_min, study_max=study_max)
        return Response(serializer.data)


class CollegeViewSet(mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.ListModelMixin,
                     BaseViewSet):
    queryset = College.objects.all()
    serializer_class = CollegeSerializer
    serializer_class_map = {
        'rank': CollegeRequestSerializer,
        # 'ranks': CollegeRequestSerializer,
        'rank_in_range': LeagueRankInRangeRequestSerializer,
        'ranks_in_range': CollegeRankInRangeRequestSerializer,
    }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(operation_description='获得此学院的排名以及学院总数, 要求为校级管理员或此学院的管理员',
                         query_serializer=CollegeRequestSerializer,
                         responses={200: RankResponseSerializer()})
    def rank(self, request):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        if not user_has_college_permission(request.user, serializer.validated_data['college_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        total = College.objects.count()
        rank = 1
        # TODO 优化这个for
        for c in College.objects.annotate(total_study=models.Sum(
                "user__total_study")).order_by('-total_study').all().iterator():
            if c.id is serializer.validated_data['college_id']:
                break
            rank += 1
        return Response({'rank': rank, 'total': total}, status=HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(operation_description='获得所有学院的信息，以及学院的学习总数，要求为校级管理员',
                         responses={200: CollegeRanksResponseSerializer(many=True)})
    def ranks(self, request):
        if not request.user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)

        queryset = College.objects.annotate(total_study=models.Sum(
            "user__total_study")).order_by('-total_study')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CollegeRanksResponseSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CollegeRanksResponseSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(operation_description='获得所有学院的信息，以及学院的学习总数，要求为校级管理员',
                         query_serializer=CollegeRankInRangeRequestSerializer,
                         responses={200: CollegeRanksResponseSerializer(many=True)})
    def ranks_in_range(self, request):
        serializer = self.get_serializer(
            data=request.query_params)
        serializer.is_valid(raise_exception=True)

        if not request.user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)

        study_min = serializer.validated_data['study_min']
        study_max = serializer.validated_data['study_max']

        queryset = College.objects.annotate(
            user_num=models.Count("user__id", distinct=True),
            total_study_in_range=models.Count(
                "user__recording__id", distinct=True, filter=models.Q(
                    user__recording__study_id__gte=study_min, user__recording__study_id__lte=study_max
                )),
        ).order_by('-total_study_in_range')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CollegeRankInRangeResponseSerializer(
                page, many=True, study_min=study_min, study_max=study_max)
            return self.get_paginated_response(serializer.data)

        serializer = CollegeRankInRangeResponseSerializer(
            queryset, many=True, study_min=study_min, study_max=study_max)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    def rank_in_range(self, request):
        serializer = self.get_serializer(
            data=request.query_params)
        serializer.is_valid(raise_exception=True)

        if not user_has_college_permission(request.user, serializer.validated_data['college_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        college_id = serializer.validated_data['college_id']
        study_min = serializer.validated_data['study_min']
        study_max = serializer.validated_data['study_max']

        queryset = College.objects.annotate(
            user_num=models.Count("user__id", distinct=True),
            total_study_in_range=models.Count(
                "user__recording__id", distinct=True, filter=models.Q(
                    user__recording__study_id__gte=study_min, user__recording__study_id__lte=study_max
                )),
        ).order_by('-total_study_in_range').get(id=college_id)

        serializer = CollegeRankInRangeResponseSerializer(
            queryset, study_min=study_min, study_max=study_max)
        return Response(serializer.data)


class LeagueBranchViewSet(mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.ListModelMixin,
                          BaseViewSet):
    queryset = LeagueBranch.objects.all()
    serializer_class = LeagueBranchSerializer
    serializer_class_map = {
        'rank': LeagueBranchRequestSerializer,
        'ranks': CollegeRequestSerializer,
        'rank_in_range': UserRankInRangeRequestSerializer,
        'ranks_in_range': LeagueRankInRangeRequestSerializer,
    }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not user_has_college_permission(request.user, serializer.validated_data["college"].id):
            return Response(status=status.HTTP_403_FORBIDDEN)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not user_has_college_permission(request.user, instance.college.id):
            return Response(status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(operation_description='获得此团支部的排名, 要求为此团支部的管理员以及上级管理员',
                         query_serializer=LeagueBranchRequestSerializer,
                         responses={200: RankResponseSerializer()})
    def rank(self, request):
        serializer = self.get_serializer(
            data=request.query_params)
        serializer.is_valid(raise_exception=True)

        u = request.user
        college_id = serializer.validated_data['college_id']
        league_branch_id = serializer.validated_data['league_branch_id']
        if not user_has_league_permission(u, college_id, league_branch_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        total = LeagueBranch.objects.count()
        rank = 1

        leagues = LeagueBranch.objects.filter(
            college=serializer.validated_data['college_id']).annotate(total_study=models.Sum(
                "user__total_study")).order_by('-total_study')
        # TODO 优化这个for
        for l in leagues.iterator():
            if l.id is serializer.validated_data['league_branch_id']:
                break
            rank += 1

        return Response({'rank': rank, 'total': total}, status=HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(operation_description='获得此学院所有团支部的信息，要求为学院管理员和校级管理员',
                         query_serializer=CollegeRequestSerializer,
                         responses={200: LeagueBranchRanksResponseSerializer(many=True)})
    def ranks(self, request):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        u = request.user
        college_id = serializer.validated_data['college_id']
        if not user_has_college_permission(u, college_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        queryset = None
        if college_id == -1:
            queryset = LeagueBranch.objects.annotate(total_study=models.Count(
                "user__recording__id")).order_by('-total_study')
        else:
            queryset = LeagueBranch.objects.filter(college=college_id).annotate(total_study=models.Count(
                "user__recording__id")).order_by('-total_study')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = LeagueBranchRanksResponseSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = LeagueBranchRanksResponseSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    def rank_in_range(self, request):
        serializer = self.get_serializer(
            data=request.query_params)
        serializer.is_valid(raise_exception=True)

        u = request.user
        college_id = serializer.validated_data['college_id']
        league_branch_id = serializer.validated_data['league_branch_id']
        study_min = serializer.validated_data['study_min']
        study_max = serializer.validated_data['study_max']

        if not user_has_league_permission(u, college_id, league_branch_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        queryset = LeagueBranch.objects.annotate(
            user_num=models.Count("user__id", distinct=True),
            total_study_in_range=models.Count(
                "user__recording__id", distinct=True, filter=models.Q(
                    user__recording__study_id__gte=study_min, user__recording__study_id__lte=study_max
                )),
        ).order_by('-total_study_in_range').get(college=college_id, id=league_branch_id)

        serializer = LeagueRankInRangeResponseSerializer(
            queryset, partial=True, study_min=study_min, study_max=study_max
        )
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(operation_description='获得此学院所有团支部的信息，要求为学院管理员和校级管理员，加入limit',
                         query_serializer=LeagueRankInRangeRequestSerializer,
                         responses={200: LeagueBranchRanksResponseSerializer(many=True)})
    def ranks_in_range(self, request):
        serializer = self.get_serializer(
            data=request.query_params)
        serializer.is_valid(raise_exception=True)

        u = request.user
        college_id = serializer.validated_data['college_id']
        study_min = serializer.validated_data['study_min']
        study_max = serializer.validated_data['study_max']

        if not user_has_college_permission(u, college_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        queryset = LeagueBranch.objects
        if college_id != -1:
            queryset = queryset.filter(
                college=college_id
            )
        queryset = queryset.annotate(
            user_num=models.Count("user__id", distinct=True),
            total_study_in_range=models.Count(
                "user__recording__id", distinct=True, filter=models.Q(
                    user__recording__study_id__gte=study_min, user__recording__study_id__lte=study_max
                )),
        ).order_by('-total_study_in_range')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = LeagueRankInRangeResponseSerializer(
                page, many=True, partial=True, study_min=study_min, study_max=study_max
            )
            return self.get_paginated_response(serializer.data)

        serializer = LeagueRankInRangeResponseSerializer(
            queryset, many=True, partial=True, study_min=study_min, study_max=study_max
        )
        return Response(serializer.data)


def check_permission(user, permission_type, permission_id):
    if (permission_type == ContentType.objects.get_for_model(College) and
            user.is_superuser):
        return True
    if (permission_type == ContentType.objects.get_for_model(LeagueBranch) and
            user_has_college_permission(user, permission_id)):
        return True
    return False


class PermissionPermissions(permissions.BasePermission):
    """
      检测User是否具有Permission的权限
    """

    def has_permission(self, request, view):
        u: User = request.user
        if u.is_anonymous:
            return False

        if view.action == 'create':
            serializer = None
            serializer = view.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            request._cached_serializer = serializer

            permission_type = serializer.validated_data["permission_type"]
            permission_id = serializer.validated_data["permission_id"]
            return check_permission(request.user, permission_type, permission_id)
        return True

    def has_object_permission(self, request, view, obj):
        return check_permission(request.user, obj.permission_type, obj.permission_id)


class PermissionViewSet(mixins.CreateModelMixin,
                        mixins.DestroyModelMixin,
                        BaseViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = (PermissionPermissions, )
