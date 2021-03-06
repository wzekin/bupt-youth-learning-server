from django.db import models
from model_utils.models import SoftDeletableModel
from young_university_study.user.models import College, User

from ..utils import get_Hashids


class Commodity(SoftDeletableModel):
    """
    商品类，用于存储商品
    """

    id = models.AutoField(primary_key=True)
    title = models.CharField("商品标题", max_length=50)
    describe = models.TextField("商品描述")
    picture = models.CharField("商品图片", null=True, max_length=100)
    location = models.CharField("兑换地点", max_length=50)

    cost = models.IntegerField("商品需要花费的积分")

    exchanged = models.IntegerField("已经兑换了的人数", default=0)
    limit = models.IntegerField("商品限额，0为不限制", default=0)

    owner = models.ForeignKey(College, on_delete=models.CASCADE, null=True)

    deadline = models.DateTimeField("截止日期")

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title


class PurchaseRecord(models.Model):
    """
    购买记录，用于记录用户的购买记录
    """

    id = models.AutoField(primary_key=True)

    customer = models.ForeignKey(User, on_delete=models.CASCADE)

    commodity = models.ForeignKey(
        Commodity, on_delete=models.CASCADE, help_text="用户购买的商品"
    )

    help_text = models.CharField(max_length=100)

    cost = models.IntegerField("用户购买商品花费的积分")

    is_exchanged = models.BooleanField("是否已经兑换", default=False)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return "%s%s" % (self.customer.__str__(), self.help_text)

    def get_code(self) -> str:
        return get_Hashids().encode(self.id)
