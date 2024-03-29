from datetime import timedelta
from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from ..user.models import College, LeagueBranch, Permission, User
from ..utils import get_Hashids
from .models import Commodity, PurchaseRecord


def setUpTestData(cls):
    cls.college1 = College.objects.create(name="test学院1")
    cls.college2 = College.objects.create(name="test学院2")
    cls.college3 = College.objects.create(name="test学院3")
    cls.league_branch1 = LeagueBranch.objects.create(
        college=cls.college1, name="test团支部1"
    )
    cls.league_branch2 = LeagueBranch.objects.create(
        college=cls.college2, name="test团支部2"
    )
    cls.league_branch3 = LeagueBranch.objects.create(
        college=cls.college2, name="test团支部3"
    )
    cls.league_branch4 = LeagueBranch.objects.create(
        college=cls.college1, name="test团支部4"
    )
    cls.user1 = User.objects.create(
        id=10001,
        name="test用户",
        identity=1,
        code="111",
        uid=111,
        college=cls.college1,
        league_branch=cls.league_branch1,
        total_study=2,
    )
    cls.user2 = User.objects.create(
        id=10003,
        name="test用户1",
        identity=1,
        code="112",
        uid=112,
        college=cls.college1,
        league_branch=cls.league_branch1,
        total_study=3,
    )
    cls.user3 = User.objects.create(
        id=10004,
        name="test用户2",
        identity=1,
        code="113",
        uid=113,
        total_score=100,
        college=cls.college2,
        league_branch=cls.league_branch2,
        total_study=3,
    )

    cls.superuser = User.objects.create(
        id=10002,
        name="super用户",
        identity=1,
        code="1111",
        uid=1111,
        is_superuser=True,
        total_study=4,
    )

    cls.commodity1 = Commodity.objects.create(
        id=1,
        title="商品1",
        describe="描述1",
        location="test location",
        picture="假装有图片",
        cost=5,
        exchanged=0,
        limit=0,
        start_time=timezone.now() - timedelta(days=1),
        deadline=timezone.now() + timedelta(days=1),
    )

    cls.commodity2 = Commodity.objects.create(
        id=2,
        title="商品2",
        describe="描述2",
        picture="假装有图片",
        cost=5,
        exchanged=0,
        limit=6,
        start_time=timezone.now() - timedelta(days=1),
        deadline=timezone.now() + timedelta(days=1),
        owner=cls.college1,
        location="test location",
    )

    cls.commodity3 = Commodity.objects.create(
        id=3,
        location="test location",
        title="商品3 已经兑换完毕",
        describe="描述3",
        picture="假装有图片",
        cost=5,
        exchanged=6,
        limit=6,
        owner=cls.college2,
        start_time=timezone.now() - timedelta(days=1),
        deadline=timezone.now() + timedelta(days=1),
    )
    cls.commodity4 = Commodity.objects.create(
        id=4,
        location="test location",
        title="商品4 过兑换时间",
        describe="描述3",
        picture="假装有图片",
        cost=5,
        exchanged=6,
        limit=6,
        owner=cls.college2,
        start_time=timezone.now() - timedelta(days=1),
        deadline=timezone.now() - timedelta(days=1),
    )
    cls.commodity5 = Commodity.objects.create(
        id=5,
        location="test location",
        title="商品5 未开始兑换",
        describe="描述3",
        picture="假装有图片",
        cost=5,
        exchanged=6,
        limit=6,
        owner=cls.college2,
        start_time=timezone.now() + timedelta(days=1),
        deadline=timezone.now() + timedelta(days=1),
    )

    Permission.objects.create(
        user_id=cls.user1,
        permission_type=ContentType.objects.get_for_model(College),
        permission_id=cls.college1.id,
    )

    Permission.objects.create(
        user_id=cls.user2,
        permission_type=ContentType.objects.get_for_model(College),
        permission_id=cls.college1.id,
    )

    PurchaseRecord.objects.create(
        id=1, commodity=cls.commodity2, customer=cls.user3, cost=6
    )


class SuperUserTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        return setUpTestData(cls)

    def setUp(self) -> None:
        self.client.force_login(user=self.superuser)

    def test_list_commdity(self):
        url = "/api/commodity/"
        response: Any = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], 1)

    def test_list_my_commdity_1(self):
        url = "/api/commodity/my_commodity/"
        response: Any = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_create_commdity(self):
        url = "/api/commodity/"
        data = {
            "title": "created",
            "location": "test location",
            "describe": "描述3",
            "cost": 5,
            "limit": 6,
            "start_time": timezone.now(),
            "deadline": timezone.now(),
        }
        response: Any = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "created")

    def test_patch_commdity_1(self):
        url = "/api/commodity/1/"
        data = {"title": "patched"}
        response: Any = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "patched")
        commodity = Commodity.objects.get(pk=1)
        self.assertEqual(commodity.title, "patched")

    def test_patch_commdity_2(self):
        url = "/api/commodity/2/"
        data = {"title": "patched"}
        response: Any = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "patched")
        commodity = Commodity.objects.get(pk=2)
        self.assertEqual(commodity.title, "patched")

    def test_patch_commdity_3(self):
        url = "/api/commodity/3/"
        data = {"title": "patched"}
        response: Any = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "patched")
        commodity = Commodity.objects.get(pk=3)
        self.assertEqual(commodity.title, "patched")

    def test_exchange_commdity_1(self):
        url = "/api/purchase/"
        data = {"commodity": 1}
        response: Any = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_purchase_exchange(self):
        code = get_Hashids().encode(1)
        url = "/api/purchase/%s/exchange/" % code
        response: Any = self.client.post(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_exchanged"], True)


class CollegeManagerUserTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        return setUpTestData(cls)

    def setUp(self) -> None:
        self.client.force_login(user=self.user1)

    def test_list_commdity(self):
        url = "/api/commodity/"
        response: Any = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_my_commdity_1(self):
        url = "/api/commodity/my_commodity/"
        response: Any = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], 2)

    def test_create_commdity(self):
        url = "/api/commodity/"
        data = {
            "title": "created",
            "describe": "描述3",
            "location": "test location",
            "cost": 5,
            "limit": 6,
            "start_time": timezone.now(),
            "deadline": timezone.now(),
        }
        response: Any = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_commdity_1(self):
        url = "/api/commodity/"
        data = {
            "title": "created",
            "describe": "描述3",
            "location": "test location",
            "owner": 1,
            "cost": 5,
            "limit": 6,
            "start_time": timezone.now(),
            "deadline": timezone.now(),
        }
        response: Any = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "created")

    def test_patch_commdity_1(self):
        url = "/api/commodity/1/"
        data = {"title": "patched"}
        response: Any = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_commdity_2(self):
        url = "/api/commodity/2/"
        data = {"title": "patched"}
        response: Any = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "patched")
        commodity = Commodity.objects.get(pk=2)
        self.assertEqual(commodity.title, "patched")

    def test_patch_commdity_3(self):
        url = "/api/commodity/3/"
        data = {"title": "patched"}
        response: Any = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_exchange_commdity_1(self):
        url = "/api/purchase/"
        data = {"commodity": 1}
        response: Any = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CommonUserTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        return setUpTestData(cls)

    def setUp(self) -> None:
        self.user3.refresh_from_db()
        self.client.force_login(user=self.user3)

    def test_list_commdity(self):
        url = "/api/commodity/"
        response: Any = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_my_commdity_1(self):
        url = "/api/commodity/my_commodity/"
        response: Any = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_commdity(self):
        url = "/api/commodity/"
        data = {
            "title": "created",
            "location": "test location",
            "describe": "描述3",
            "cost": 5,
            "limit": 6,
        }
        response: Any = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_commdity_1(self):
        url = "/api/commodity/1/"
        data = {"title": "patched"}
        response: Any = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_commdity_2(self):
        url = "/api/commodity/2/"
        data = {"title": "patched"}
        response: Any = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_commdity_3(self):
        url = "/api/commodity/3/"
        data = {"title": "patched"}
        response: Any = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_exchange_commdity_1(self):
        url = "/api/purchase/"
        data = {"commodity": 1}
        response: Any = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        old_score = self.user3.total_score
        self.user3.refresh_from_db()
        self.assertEqual(self.user3.total_score, old_score - self.commodity1.cost)

    def test_exchange_commdity_2(self):
        url = "/api/purchase/"
        data = {"commodity": 3}
        response: Any = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_exchange_commdity_3(self):
        url = "/api/purchase/"
        data = {"commodity": 4}
        response: Any = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_exchange_commdity_4(self):
        url = "/api/purchase/"
        data = {"commodity": 5}
        response: Any = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_purchase(self):
        code = get_Hashids().encode(1)
        url = "/api/purchase/%s/" % code
        response: Any = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], code)

    def test_purchase_1(self):
        url = "/api/purchase/22222/"
        response: Any = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
