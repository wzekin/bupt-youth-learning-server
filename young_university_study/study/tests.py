from young_university_study.study.models import StudyRecording
from rest_framework.test import APITestCase
from rest_framework import status
from typing import Any
from .models import *
from ..user.models import *


class StudyPeriodTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.study_period1 = StudyPeriod.objects.create(season=1, period=1, name='test1', url='url')
        cls.study_period2 = StudyPeriod.objects.create(season=1, period=2, name='test2', url='url')
        cls.user1 = User.objects.create(id =10001, name="test用户", identity=1, code='111', uid=111, total_study=2)
        cls.superuser = User.objects.create(id =10002, name="super用户", identity=1, code='1111', uid=1111, is_superuser=True, total_study=4)

    def setUp(self):
        self.client.force_login(user=self.superuser)

    def test_period_create(self):
        url = '/api/study_period/'
        data = {'season':1,'period':3, 'name':'test3', 'url':'url'}
        response:Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StudyPeriod.objects.count(), 3)

    def test_period_destory(self):
        url = '/api/study_period/2/'
        response:Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(StudyPeriod.objects.get().id, 1)

    def test_period_list(self):
        url = '/api/study_period/'
        response:Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_period_lastst(self):
        url = '/api/study_period/lastst/'
        response:Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 2)

class StudyPeriodCommonUserTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.study_period1 = StudyPeriod.objects.create(season=1, period=1, name='test1', url='url')
        cls.study_period2 = StudyPeriod.objects.create(season=1, period=2, name='test2', url='url')
        cls.user1 = User.objects.create(id =10001, name="test用户", identity=1, code='111', uid=111, total_study=2)
        cls.superuser = User.objects.create(id =10002, name="super用户", identity=1, code='1111', uid=1111, is_superuser=True, total_study=4)

    def setUp(self):
        self.client.force_login(user=self.user1)

    def test_period_create(self):
        url = '/api/study_period/'
        data = {'season':1,'period':3, 'name':'test3', 'url':'url'}
        response:Any = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_period_destory(self):
        url = '/api/study_period/2/'
        response:Any = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_period_list(self):
        url = '/api/study_period/'
        response:Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_period_lastst(self):
        url = '/api/study_period/lastst/'
        response:Any = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class StudyRecordingTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.study_period1 = StudyPeriod.objects.create(season=1, period=1, name='test1', url='url')
        cls.study_period2 = StudyPeriod.objects.create(season=1, period=2, name='test2', url='url')
        cls.study_period3 = StudyPeriod.objects.create(season=1, period=2, name='test2', url='url')
        cls.study_period4 = StudyPeriod.objects.create(season=1, period=2, name='test2', url='url')
        cls.study_period5 = StudyPeriod.objects.create(season=1, period=2, name='test2', url='url')
        cls.study_period6 = StudyPeriod.objects.create(season=1, period=2, name='test2', url='url')
        cls.user1 = User.objects.create(id =10001, name="test用户", identity=1, code='111', uid=111, total_study=2)
        cls.superuser = User.objects.create(id =10002, name="super用户", identity=1, code='1111', uid=1111, is_superuser=True, total_study=4)

    def setUp(self):
        self.client.force_login(user=self.superuser)

    def test_create(self):
        url = '/api/study_recording/'
        response:Any = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['score'], 1)

        response:Any = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create1(self):
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period1, score=1)
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period2, score=1)
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period3, score=1)
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period4, score=1)
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period5, score=1)

        url = '/api/study_recording/'
        response:Any = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['score'], 5)
        self.assertEqual(response.data['detail'], '连续学习6期')

    def test_create2(self):
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period1, score=1)
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period2, score=1)
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period3, score=1)
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period5, score=1)

        url = '/api/study_recording/'
        response:Any = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['score'], 2)
        self.assertEqual(response.data['detail'], '连续学习2期')

    def test_create3(self):
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period1, score=1)
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period3, score=1)
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period4, score=1)
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period5, score=1)

        url = '/api/study_recording/'
        response:Any = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['score'], 4)
        self.assertEqual(response.data['detail'], '连续学习4期')

    def test_create4(self):
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period1, score=1)
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period3, score=1)
        StudyRecording.objects.create(user_id=self.superuser, study_id=self.study_period4, score=1)

        url = '/api/study_recording/'
        response:Any = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['score'], 1)
        self.assertEqual(response.data['detail'], '连续学习1期')
