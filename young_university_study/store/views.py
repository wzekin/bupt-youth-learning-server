import os

import nanoid
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.http.response import HttpResponseForbidden
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response

from ..user.models import College, User, user_has_college_permission
from ..utils import get_Hashids
from .models import Commodity, PurchaseRecord
from .serializers import (
    CommoditySerializers,
    PurchaseRecordListSerializers,
    PurchaseRecordSerializers,
)


class CommodityViewSetPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            # 先校验登录态
            user.is_authenticated
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
        return user.is_authenticated and (
            request.method in SAFE_METHODS
            or user.is_superuser
            or (obj.owner and user_has_college_permission(user, obj.owner.id))
        )


class CommodityViewSet(
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = Commodity.all_objects.all()
    serializer_class = CommoditySerializers
    permission_classes = [CommodityViewSetPermission]

    def list(self, request, *args, **kwargs):
        user: User = request.user
        queryset = Commodity.available_objects.filter(
            Q(owner__isnull=True) | Q(owner=user.college)
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # 展示由自己创建的所有的商品
    @action(methods=["GET"], detail=False)
    def my_commodity(self, request):
        user: User = request.user

        if user.is_superuser:
            queryset = Commodity.all_objects.all()
        else:
            queryset = Commodity.all_objects.raw(
                "SELECT pr.* from store_commodity as pr "
                "inner join user_permission p on pr.owner_id = p.permission_id "
                "where p.user_id_id = %s and p.permission_type_id = %s",
                [
                    str(user.id),
                    str(ContentType.objects.get_for_model(College).id),
                ],
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PurchaseViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    queryset = PurchaseRecord.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return PurchaseRecordSerializers
        else:
            return PurchaseRecordListSerializers

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

    def retrieve(self, request, *args, **kwargs):
        self.kwargs["pk"] = get_Hashids().decode(self.kwargs["pk"])[0]
        return super().retrieve(request, *args, **kwargs)

    @action(methods=["post"], detail=True)
    def exchange(self, request):
        self.kwargs["pk"] = get_Hashids().decode(self.kwargs["pk"])[0]
        record = self.get_object()
        record.is_exchanged = True
        record.save()
        serializer = self.get_serializer(record)
        return Response(serializer.data)


def upload_image(request):
    user = request.user
    if not (
        user.is_authenticated
        and (
            # 只有超级管理员和院管理员可以创建
            user.is_superuser
            or user.permissions.filter(
                permission_type=ContentType.objects.get_for_model(College),
            ).exists()
        )
    ):
        return HttpResponseForbidden()
    data = {}
    for key, file in request.FILES.items():
        if not file.content_type.startswith("image"):
            data[key] = u"请输入正确的格式！"
        elif file.size > 1024 * 1024:
            data[key] = u"图片大小要求1M以内"
        else:
            filename = nanoid.generate() + "_" + file.name
            with open(
                os.path.join(settings.BASE_DIR, "media", "store", filename),
                "wb",
            ) as f:
                f.write(file.read())
            data[key] = os.path.join("static", "store", filename)

    return JsonResponse(data)
