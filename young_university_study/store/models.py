from django.db import models
from young_university_study.user.models import User


class Commodity(models.Model):
    """
    商品类，用于存储商品
    """

    id = models.AutoField(primary_key=True)
    title = models.CharField("商品标题", max_length=50)
    describe = models.TextField("商品描述")
    picture = models.ImageField("商品图片", null=True, upload_to="commodity")

    cost = models.IntegerField("商品需要花费的积分")

    exchanged = models.IntegerField("已经兑换了的人数", default=0)
    limit = models.IntegerField("商品限额，0为不限制", default=0)

    owner = models.ForeignKey(User, on_delete=models.CASCADE)

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

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return "%s%s" % (self.customer.__str__(), self.help_text)