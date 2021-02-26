from rest_framework import serializers

from .models import Commodity, PurchaseRecord


class CommoditySerializers(serializers.ModelSerializer):
    class Meta:
        model = Commodity
        fields = [
            "id",
            "title",
            "describe",
            "cost",
            "exchanged",
            "picture",
            "limit",
            "owner",
            "updated",
            "created",
        ]
        read_only_fields = ["id", "owner", "updated", "created", "exchanged"]

    def create(self, validated_data):
        return Commodity.objects.create(
            owner=self.context["request"].user, **validated_data
        )


class PurchaseRecordSerializers(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRecord
        fields = ["id", "commodity", "cost", "help_text", "created"]
        read_only_fields = ["id", "cost", "help_text", "created"]

    def create(self, validated_data):
        commodity: Commodity = validated_data["commodity"]
        return PurchaseRecord.objects.create(
            customer=self.context["request"].user,
            help_text="花费%d积分购买%s" % (commodity.cost, commodity.title),
            cost=commodity.cost,
            **validated_data,
        )
