from django.contrib.contenttypes.models import ContentType
from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.test import APITestCase
from typing import Any
from .models import User, College, LeagueBranch, Permission,  user_has_league_permission, user_has_college_permission
from ..study.models import StudyPeriod, StudyRecording


def setUpTestData(cls):
    cls.college1 = College.objects.create(name="test学院1")
    cls.college2 = College.objects.create(name="test学院2")
    cls.college3 = College.objects.create(name="test学院3")
    cls.league_branch1 = LeagueBranch.objects.create(
        college=cls.college1, name="test团支部1")
    cls.league_branch2 = LeagueBranch.objects.create(
        college=cls.college2, name="test团支部2")
    cls.league_branch3 = LeagueBranch.objects.create(
        college=cls.college2, name="test团支部3")
    cls.user1 = User.objects.create(id=10001, name="test用户", identity=1, code='111',
                                    uid=111, college=cls.college1, league_branch=cls.league_branch1, total_study=2)
    cls.user2 = User.objects.create(id=10003, name="test用户1", identity=1, code='112',
                                    uid=112, college=cls.college1, league_branch=cls.league_branch1, total_study=3)
    cls.user3 = User.objects.create(id=10004, name="test用户2", identity=1, code='113',
                                    uid=113, college=cls.college2, league_branch=cls.league_branch2, total_study=3)
    cls.study_period1 = StudyPeriod.objects.create(
        season=1, period=1, name='test1', url='url')
    cls.study_period2 = StudyPeriod.objects.create(
        season=1, period=2, name='test2', url='url')
    cls.superuser = User.objects.create(
        id=10002, name="super用户", identity=1, code='1111', uid=1111, is_superuser=True, total_study=4)

    Permission.objects.create(user_id=cls.user1, permission_type=ContentType.objects.get_for_model(
        College), permission_id=cls.college1.id)
    StudyRecording.objects.create(
        user_id=cls.user1, study_id=cls.study_period1, score=1)
    StudyRecording.objects.create(
        user_id=cls.user1, study_id=cls.study_period2, score=1)
    StudyRecording.objects.create(
        user_id=cls.user2, study_id=cls.study_period2, score=1)
    StudyRecording.objects.create(
        user_id=cls.user3, study_id=cls.study_period1, score=1)


class UserPermissionTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.college1 = College.objects.create(name="test学院1")
        cls.college2 = College.objects.create(name="test学院2")
        cls.league_branch1 = LeagueBranch.objects.create(
            college=cls.college1, name="test团支部1")
        cls.league_branch2 = LeagueBranch.objects.create(
            college=cls.college2, name="test团支部2")
        cls.user1 = User.objects.create(id=10001, name="test用户", identity=1, code='111',
                                        uid=111, college=cls.college1, league_branch=cls.league_branch1)
        cls.superuser = User.objects.create(
            id=10002, name="super用户", identity=1, code='1111', uid=1111, is_superuser=True)
        Permission.objects.create(user_id=cls.user1, permission_type=ContentType.objects.get_for_model(
            College), permission_id=cls.college1.id)
        Permission.objects.create(user_id=cls.user1, permission_type=ContentType.objects.get_for_model(
            LeagueBranch), permission_id=cls.league_branch2.id)

    def test_user_has_college_permission(self):
        self.assertTrue(user_has_college_permission(
            self.user1, self.college1.id))
        self.assertFalse(user_has_college_permission(
            self.user1, self.college2.id))
        self.assertTrue(user_has_college_permission(
            self.superuser, self.college2.id))
        self.assertTrue(user_has_college_permission(
            self.superuser, self.college1.id))

    def test_user_has_league_permission(self):
        self.assertTrue(user_has_league_permission(
            self.user1, self.college1.id, self.league_branch1.id))
        self.assertTrue(user_has_league_permission(
            self.user1, self.college2.id, self.league_branch2.id))
        self.assertTrue(user_has_league_permission(
            self.superuser, self.college1.id, self.league_branch1.id))
        self.assertTrue(user_has_league_permission(
            self.superuser, self.college2.id, self.league_branch2.id))


class SuperUserTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        setUpTestData(cls)

    def setUp(self) -> None:
        self.client.force_login(user=self.superuser)

    def test_user_me_get(self):
        url = '/api/user/me/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 10002)
        self.assertEqual(response.data['name'], 'super用户')
        self.assertEqual(response.data['identity'], 1)
        self.superuser.refresh_from_db()
        self.assertEqual(self.superuser.college, None)

    def test_user_me_put(self):
        url = '/api/user/me/'
        response: Any = self.client.put(
            url, data={'college': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['college'], 1)
        self.superuser.refresh_from_db()
        self.assertEqual(self.superuser.college.id, 1)
        self.assertEqual(self.superuser.league_branch, None)

    def test_user_rank(self):
        url = '/api/user/rank/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'rank': 1, 'total': 4})

    def test_user_ranks(self):
        url = '/api/user/ranks/?league_branch_id=1&college_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertTrue('total_study' in response.data[0])

    def test_user_ranks_in_range_1(self):
        url = '/api/user/ranks_in_range/?league_branch_id=1&college_id=1&study_min=1&study_max=2'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertTrue('total_study_in_range' in response.data[0])
        self.assertEqual(response.data[0]['id'], self.user1.id)
        self.assertEqual(response.data[0]['total_study_in_range'], 2)
        self.assertEqual(response.data[1]['id'], self.user2.id)
        self.assertEqual(response.data[1]['total_study_in_range'], 1)

    def test_user_ranks_in_range_2(self):
        url = '/api/user/ranks_in_range/?league_branch_id=1&college_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertTrue('total_study_in_range' in response.data[0])
        self.assertEqual(response.data[0]['total_study_in_range'], 1)
        self.assertEqual(response.data[1]['total_study_in_range'], 0)

    def test_college_create(self):
        url = '/api/college/'
        data = {'name': 'test create学院'}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['id'], 4)
        self.assertEqual(response.data['name'], data['name'])
        self.assertEqual(College.objects.count(), 4)

    def test_college_destory(self):
        url = '/api/college/3/'
        response: Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(College.objects.count(), 2)

    def test_college_destory_failed(self):
        url = '/api/college/1/'
        self.assertRaises(ProtectedError, self.client.delete,
                          url, format='json')

    def test_college_list(self):
        url = '/api/college/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_college_rank(self):
        url = '/api/college/rank/?college_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'rank': 1, 'total': 3})

    def test_college_ranks(self):
        url = '/api/college/ranks/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertTrue('total_study' in response.data[0])

    def test_college_rank_in_range(self):
        url = '/api/college/rank_in_range/?college_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('total_study_in_range' in response.data)
        self.assertEqual(response.data['user_num'], 2)

    def test_college_ranks_in_range(self):
        url = '/api/college/ranks_in_range/?study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('total_study_in_range' in response.data[0])
        self.assertEqual(response.data[0]['finish_rate'], 0.5)

    def test_league_branch_create(self):
        url = '/api/league_branch/'
        data = {'name': 'test create学院', 'college': 1}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.data['id'], 4)
        self.assertEqual(response.data['name'], data['name'])
        self.assertEqual(LeagueBranch.objects.count(), 4)

    def test_league_branch_destory(self):
        url = '/api/league_branch/3/'
        response: Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(LeagueBranch.objects.count(), 2)

    def test_league_branch_list(self):
        url = '/api/league_branch/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_league_branch_rank(self):
        url = '/api/league_branch/rank/?college_id=1&league_branch_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'rank': 1, 'total': 3})

    def test_league_branch_ranks(self):
        url = '/api/league_branch/ranks/?college_id=2'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertTrue('total_study' in response.data[0])

    def test_league_branch_rank_in_range(self):
        url = '/api/league_branch/rank_in_range/?college_id=1&league_branch_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('total_study_in_range' in response.data)
        self.assertEqual(response.data['user_num'], 2)

    def test_league_branch_ranks_in_range(self):
        url = '/api/league_branch/ranks_in_range/?college_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('total_study_in_range' in response.data[0])
        self.assertEqual(response.data[0]['finish_rate'], 0.5)

    def test_permission_create(self):
        url = '/api/permission/'
        data = {'user_id': 10003, 'permission_type': ContentType.objects.get_for_model(
            LeagueBranch).id, 'permission_id': 1}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(user_has_league_permission(self.user2, 0, 1))

    def test_permission_destory(self):
        url = '/api/permission/1/'
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(user_has_college_permission(self.user1, 1))


class CollegeAdminUserTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        setUpTestData(cls)
        Permission.objects.create(user_id=cls.user2, permission_type=ContentType.objects.get_for_model(
            College), permission_id=cls.college1.id)

    def setUp(self) -> None:
        self.client.force_login(user=self.user2)

    def test_user_me_get(self):
        url = '/api/user/me/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_me_put(self):
        url = '/api/user/me/'
        response: Any = self.client.put(
            url, data={'college': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_rank(self):
        url = '/api/user/rank/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_ranks(self):
        url = '/api/user/ranks/?league_branch_id=1&college_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_ranks_1(self):
        url = '/api/user/ranks/?league_branch_id=2&college_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_ranks_in_range_1(self):
        url = '/api/user/ranks_in_range/?league_branch_id=1&college_id=1&study_min=1&study_max=2'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_ranks_in_range_2(self):
        url = '/api/user/ranks_in_range/?league_branch_id=2&college_id=1&study_min=1&study_max=2'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_create(self):
        url = '/api/college/'
        data = {'name': 'test create学院'}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_destory(self):
        url = '/api/college/3/'
        response: Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_list(self):
        url = '/api/college/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_college_rank_1(self):
        url = '/api/college/rank/?college_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_college_rank_2(self):
        url = '/api/college/rank/?college_id=2'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_ranks(self):
        url = '/api/college/ranks/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_rank_in_range_1(self):
        url = '/api/college/rank_in_range/?college_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_college_rank_in_range_2(self):
        url = '/api/college/rank_in_range/?college_id=2&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_ranks_in_range(self):
        url = '/api/college/ranks_in_range/?study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_create(self):
        url = '/api/league_branch/'
        data = {'name': 'test create学院', 'college': 1}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_league_branch_create(self):
        url = '/api/league_branch/'
        data = {'name': 'test create学院', 'college': 2}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_destory(self):
        url = '/api/league_branch/3/'
        response: Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_list(self):
        url = '/api/league_branch/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_league_branch_rank_1(self):
        url = '/api/league_branch/rank/?college_id=1&league_branch_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_league_branch_rank_2(self):
        url = '/api/league_branch/rank/?college_id=1&league_branch_id=2'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_ranks_1(self):
        url = '/api/league_branch/ranks/?college_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_league_branch_ranks_2(self):
        url = '/api/league_branch/ranks/?college_id=2'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_rank_in_range_1(self):
        url = '/api/league_branch/rank_in_range/?college_id=1&league_branch_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_league_branch_rank_in_range_2(self):
        url = '/api/league_branch/rank_in_range/?college_id=1&league_branch_id=2&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_ranks_in_range_1(self):
        url = '/api/league_branch/ranks_in_range/?college_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_league_branch_ranks_in_range_2(self):
        url = '/api/league_branch/ranks_in_range/?college_id=2&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_create_1(self):
        url = '/api/permission/'
        data = {'user_id': 10003, 'permission_type': ContentType.objects.get_for_model(
            LeagueBranch).id, 'permission_id': 1}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_permission_create_2(self):
        url = '/api/permission/'
        data = {'user_id': 10003, 'permission_type': ContentType.objects.get_for_model(
            LeagueBranch).id, 'permission_id': 2}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_destory(self):
        url = '/api/permission/1/'
        response: Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class LeagueBranchUserTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        setUpTestData(cls)
        Permission.objects.create(user_id=cls.user2, permission_type=ContentType.objects.get_for_model(
            LeagueBranch), permission_id=cls.league_branch1.id)

    def setUp(self) -> None:
        self.client.force_login(user=self.user2)

    def test_user_me_get(self):
        url = '/api/user/me/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_me_put(self):
        url = '/api/user/me/'
        response: Any = self.client.put(
            url, data={'college': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_rank(self):
        url = '/api/user/rank/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_ranks_1(self):
        url = '/api/user/ranks/?league_branch_id=1&college_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_ranks_2(self):
        url = '/api/user/ranks/?league_branch_id=2&college_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_ranks_in_range_1(self):
        url = '/api/user/ranks_in_range/?league_branch_id=1&college_id=1&study_min=1&study_max=2'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_ranks_in_range_2(self):
        url = '/api/user/ranks_in_range/?league_branch_id=2&college_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_create(self):
        url = '/api/college/'
        data = {'name': 'test create学院'}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_destory(self):
        url = '/api/college/3/'
        response: Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_list(self):
        url = '/api/college/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_college_rank(self):
        url = '/api/college/rank/?college_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_ranks(self):
        url = '/api/college/ranks/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_rank_in_range(self):
        url = '/api/college/rank_in_range/?college_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_ranks_in_range(self):
        url = '/api/college/ranks_in_range/?study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_create(self):
        url = '/api/league_branch/'
        data = {'name': 'test create学院', 'college': 1}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_destory(self):
        url = '/api/league_branch/3/'
        response: Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_list(self):
        url = '/api/league_branch/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_league_branch_rank_1(self):
        url = '/api/league_branch/rank/?college_id=1&league_branch_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_league_branch_rank_2(self):
        url = '/api/league_branch/rank/?college_id=1&league_branch_id=2'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_ranks(self):
        url = '/api/league_branch/ranks/?college_id=2'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_rank_in_range_1(self):
        url = '/api/league_branch/rank_in_range/?college_id=1&league_branch_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_league_branch_rank_in_range(self):
        url = '/api/league_branch/rank_in_range/?college_id=1&league_branch_id=2&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_ranks_in_range(self):
        url = '/api/league_branch/ranks_in_range/?college_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_create(self):
        url = '/api/permission/'
        data = {'user_id': 10003, 'permission_type': ContentType.objects.get_for_model(
            LeagueBranch).id, 'permission_id': 2}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_destory(self):
        url = '/api/permission/1/'
        response: Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CommonUserTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        setUpTestData(cls)

    def setUp(self) -> None:
        self.client.force_login(user=self.user2)

    def test_user_me_get(self):
        url = '/api/user/me/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_me_put(self):
        url = '/api/user/me/'
        response: Any = self.client.put(
            url, data={'college': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_rank(self):
        url = '/api/user/rank/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_ranks(self):
        url = '/api/user/ranks/?league_branch_id=1&college_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_ranks_in_range_1(self):
        url = '/api/user/ranks_in_range/?league_branch_id=1&college_id=1&study_min=1&study_max=2'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_ranks_in_range_2(self):
        url = '/api/user/ranks_in_range/?league_branch_id=1&college_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_create(self):
        url = '/api/college/'
        data = {'name': 'test create学院'}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_destory(self):
        url = '/api/college/3/'
        response: Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_list(self):
        url = '/api/college/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_college_rank(self):
        url = '/api/college/rank/?college_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_ranks(self):
        url = '/api/college/ranks/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_rank_in_range(self):
        url = '/api/college/rank_in_range/?college_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_ranks_in_range(self):
        url = '/api/college/ranks_in_range/?study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_create(self):
        url = '/api/league_branch/'
        data = {'name': 'test create学院', 'college': 1}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_destory(self):
        url = '/api/league_branch/3/'
        response: Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_list(self):
        url = '/api/league_branch/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_league_branch_rank(self):
        url = '/api/league_branch/rank/?college_id=1&league_branch_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_ranks(self):
        url = '/api/league_branch/ranks/?college_id=2'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_rank_in_range(self):
        url = '/api/league_branch/rank_in_range/?college_id=1&league_branch_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_ranks_in_range(self):
        url = '/api/league_branch/ranks_in_range/?college_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_create(self):
        url = '/api/permission/'
        data = {'user_id': 10003, 'permission_type': ContentType.objects.get_for_model(
            LeagueBranch).id, 'permission_id': 1}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_destory(self):
        url = '/api/permission/1/'
        response: Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AnonymousUserTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        setUpTestData(cls)

    def setUp(self) -> None:
        pass

    def test_user_me_get(self):
        url = '/api/user/me/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_me_put(self):
        url = '/api/user/me/'
        response: Any = self.client.put(
            url, data={'college': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_rank(self):
        url = '/api/user/rank/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_ranks(self):
        url = '/api/user/ranks/?league_branch_id=1&college_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_ranks_in_range_1(self):
        url = '/api/user/ranks_in_range/?league_branch_id=1&college_id=1&study_min=1&study_max=2'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_ranks_in_range_2(self):
        url = '/api/user/ranks_in_range/?league_branch_id=1&college_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_create(self):

        url = '/api/college/'
        data = {'name': 'test create学院'}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_destory(self):
        url = '/api/college/3/'
        response: Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_list(self):
        url = '/api/college/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_college_rank(self):
        url = '/api/college/rank/?college_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_ranks(self):
        url = '/api/college/ranks/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_rank_in_range(self):
        url = '/api/college/rank_in_range/?college_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_ranks_in_range(self):
        url = '/api/college/ranks_in_range/?study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_create(self):
        url = '/api/league_branch/'
        data = {'name': 'test create学院', 'college': 1}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_destory(self):
        url = '/api/league_branch/3/'
        response: Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_list(self):
        url = '/api/league_branch/'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_league_branch_rank(self):
        url = '/api/league_branch/rank/?college_id=1&league_branch_id=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_ranks(self):
        url = '/api/league_branch/ranks/?college_id=2'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_rank_in_range(self):
        url = '/api/league_branch/rank_in_range/?college_id=1&league_branch_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_league_branch_ranks_in_range(self):
        url = '/api/league_branch/ranks_in_range/?college_id=1&study_min=1&study_max=1'
        response: Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_create(self):
        url = '/api/permission/'
        data = {'user_id': 10003, 'permission_type': ContentType.objects.get_for_model(
            LeagueBranch).id, 'permission_id': 1}
        response: Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_destory(self):
        url = '/api/permission/1/'
        response: Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
