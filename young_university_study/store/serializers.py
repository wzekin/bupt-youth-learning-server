from rest_framework import fields, serializers

from ..user.models import User, user_has_college_permission
from .models import Commodity, PurchaseRecord


class CommoditySerializers(serializers.ModelSerializer):
    class Meta:
        model = Commodity
        fields = [
            "id",
            "title",
            "describe",
            "cost",
            "start_time",
            "deadline",
            "location",
            "exchanged",
            "picture",
            "limit",
            "owner",
            "is_removed",
            "updated",
            "created",
        ]
        read_only_fields = ["id", "updated", "created", "exchanged"]

    def create(self, validated_data):
        return Commodity.objects.create(**validated_data)

    def validate(self, data):
        """
        检查是否有权限创建此商品
        """
        # 部分更新时不进行校验
        if self.partial:
            return data
        user: User = self.context["request"].user
        if not data.get("owner", None) and not user.is_superuser:
            raise serializers.ValidationError("只有superuser能创建校级商品")
        elif data.get("owner", None) and not user_has_college_permission(
            user, data["owner"].id
        ):
            raise serializers.ValidationError("没有创建此商品的权限")
        return data


class CommoditySerializersForPurchase(serializers.ModelSerializer):
    class Meta:
        model = Commodity
        fields = [
            "id",
            "title",
            "deadline",
            "location",
            "picture",
            "updated",
            "created",
        ]


class UserSerializersForPurchase(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "name",
        ]


class PurchaseRecordSerializers(serializers.ModelSerializer):
    code = fields.CharField(source="get_code", read_only=True)

    class Meta:
        model = PurchaseRecord
        fields = [
            "commodity",
            "cost",
            "help_text",
            "updated",
            "created",
            "code",
            "customer",
            "is_exchanged",
        ]
        read_only_fields = [
            "cost",
            "help_text",
            "updated",
            "created",
            "code",
            "customer",
            "is_exchanged",
        ]

    def create(self, validated_data):
        commodity: Commodity = validated_data["commodity"]
        return PurchaseRecord.objects.create(
            customer=self.context["request"].user,
            help_text="花费%d积分购买%s" % (commodity.cost, commodity.title),
            cost=commodity.cost,
            **validated_data,
        )


class PurchaseRecordListSerializers(PurchaseRecordSerializers):
    commodity = CommoditySerializersForPurchase()
    customer = UserSerializersForPurchase()
