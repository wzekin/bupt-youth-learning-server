from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from young_university_study.user.models import College, User

from .models import Commodity, PurchaseRecord
from .serializers import CommoditySerializers, PurchaseRecordSerializers


class CommodityViewSetPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            # 先校验登录态
            request.user.is_authenticated
            and (
                # 如果是查找，直接通过
                request.method in SAFE_METHODS
                # 只有超级管理员和院管理员可以创建
                or user.is_superuser
                or user.permissions.filter(
                    permission_type=ContentType.objects.get_for_model(College),
                ).exists()
            )
        )

    def has_object_permission(self, request, view, obj: Commodity):
        # 超级管理员和修改和删除
        user: User = request.user
        return user.is_superuser or obj.owner == user


class CommodityViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
):
    queryset = Commodity.objects.all()
    serializer_class = CommoditySerializers
    permission_classes = [CommodityViewSetPermission]

    # 展示由自己创建的所有的商品
    @action(methods=["GET"], detail=False)
    def my_commodity(self, request):
        queryset = self.get_queryset().filter(owner=request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PurchaseViewSet(
    viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin
):
    queryset = PurchaseRecord.objects.all()
    serializer_class = PurchaseRecordSerializers
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(customer=self.request.user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        commodity: Commodity = Commodity.objects.select_for_update().get(
            pk=serializer.validated_data["commodity"].id
        )
        user: User = User.objects.select_for_update().get(pk=request.user.id)
        if user.total_score < commodity.cost:
            return Response("您的积分不足", status.HTTP_400_BAD_REQUEST)
        if commodity.limit > 0 and commodity.exchanged >= commodity.limit:
            return Response("商品已换完", status.HTTP_400_BAD_REQUEST)
        user.total_score -= commodity.cost
        user.save()
        commodity.exchanged += 1
        commodity.save()
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )