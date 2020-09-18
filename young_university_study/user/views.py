from django.contrib.auth import login
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes
from rest_framework.status import HTTP_200_OK
from django.core.exceptions import ObjectDoesNotExist
from drf_yasg.utils import swagger_auto_schema
from .models import *
from .serializers import *


class UserViewSetPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # 只有校级管理员可以创建
        if view.action == 'list':
            return request.user.is_superuser
        return True

    def has_object_permission(self, request, view, obj):
        # 只有校级管理员以及学院管理员可以修改
        if view.action in ('update', 'partial_update', 'retrieve'):
            return request.user.is_superuser or request.user is obj
        # 只有校级管理员可以删除
        if view.action == 'destory':
            return request.user.is_superuser
        return True


class UserViewSet(
        mixins.ListModelMixin,
        mixins.UpdateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.CreateModelMixin,
        viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = (UserViewSetPermission,)

    def get_serializer_class(self):
        if self.request.method == 'PUT' and self.action == 'me':
            return UserUpdateSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'login':
            return UserLoginSerializer
        else:
            return UserSerializer

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
            serializer = self.get_serializer(u)
            return Response(serializer.data)
        if request.method == 'PUT':
            serializer = self.get_serializer(
                u, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(u, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                u._prefetched_objects_cache = {}

            return Response(serializer.data)
        return Response(status=status.HTTP_400_BAD_REQUEST)

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
                         query_serializer=LeagueBranchRankRequestSerializer,
                         responses={200: UserRankResponseSerializer(many=True)})
    def ranks(self, request):
        serializer = LeagueBranchRankRequestSerializer(
            data=request.query_params)
        serializer.is_valid(raise_exception=True)

        u = request.user
        college_id = serializer.validated_data['college_id']
        league_branch_id = serializer.validated_data['league_branch_id']

        if not request.user.is_superuser and not user_has_college_permission(u, college_id) and not user_has_league_permission(u, league_branch_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        queryset = User.objects.filter(
            college=college_id, league_branch=league_branch_id).select_related("college").select_related("league_branch").prefetch_related("permissions")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CollegeViewSet(mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    queryset = College.objects.all()
    serializer_class = CollegeSerializer

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
                         query_serializer=CollegeRankRequestSerializer,
                         responses={200: RankResponseSerializer()})
    def rank(self, request):
        serializer = CollegeRankRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        if not request.user.is_superuser and not user_has_college_permission(request.user, serializer.validated_data['college_id']):
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


class LeagueBranchViewSet(mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    queryset = LeagueBranch.objects.all()
    serializer_class = LeagueBranchSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.is_superuser and not user_has_college_permission(request.user, serializer.validated_data["college"].id):
            return Response(status=status.HTTP_403_FORBIDDEN)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_superuser and not user_has_college_permission(request.user, instance.college.id):
            return Response(status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(operation_description='获得此团支部的排名, 要求为此团支部的管理员以及上级管理员',
                         query_serializer=LeagueBranchRankRequestSerializer,
                         responses={200: RankResponseSerializer()})
    def rank(self, request):
        u = request.user
        serializer = LeagueBranchRankRequestSerializer(
            data=request.query_params)
        serializer.is_valid(raise_exception=True)

        if (not request.user.is_superuser and
            not user_has_college_permission(u, serializer.validated_data['college_id']) and
                not user_has_league_permission(u, serializer.validated_data['league_branch_id'])):
            # 判断是否有足够的权限
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
                         query_serializer=CollegeRankRequestSerializer,
                         responses={200: CollegeRanksResponseSerializer(many=True)})
    def ranks(self, request):
        serializer = CollegeRankRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        college_id = serializer.validated_data['college_id']
        if (not request.user.is_superuser and
                not user_has_college_permission(request.user, college_id)):

            return Response(status=status.HTTP_403_FORBIDDEN)

        queryset = None
        if college_id == -1:
            queryset = LeagueBranch.objects.annotate(total_study=models.Sum(
                "user__total_study")).order_by('-total_study')
        else:
            queryset = LeagueBranch.objects.filter(college=college_id).annotate(total_study=models.Sum(
                "user__total_study")).order_by('-total_study')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CollegeRanksResponseSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CollegeRanksResponseSerializer(queryset, many=True)
        return Response(serializer.data)


def check_permission(user, permission_type, permission_id):
    if (permission_type == ContentType.objects.get_for_model(College) and
            user.is_superuser):
        return True
    if (permission_type == ContentType.objects.get_for_model(LeagueBranch) and
            (user.is_superuser or user_has_college_permission(user, permission_id))):
        return True
    return False


class PermissionViewSet(mixins.CreateModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not check_permission(request.user, serializer.validated_data["permission_type"], serializer.validated_data["permission_id"]):
            return Response(status=status.HTTP_403_FORBIDDEN)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not check_permission(request.user, instance.permission_type, instance.permission_id):
            return Response(status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
