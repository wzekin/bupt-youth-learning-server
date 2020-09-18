from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from ..user.models import user_has_college_permission
from drf_yasg.utils import swagger_auto_schema
from .models import *
from .serializers import *
# import grpc
import django_excel as excel
# from .grpc import api_pb2_grpc, api_pb2


class StudyPeriodViewSetPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # 只有校级管理员可以创建
        if view.action == 'create':
            return request.user.is_superuser
        return True

    def has_object_permission(self, request, view, obj):
        # 只有校级管理员可以删除
        if view.action == 'destory':
            return request.user.is_superuser
        return True


class StudyPeriodViewSet(mixins.CreateModelMixin,
                         mixins.DestroyModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    queryset = StudyPeriod.objects.all()
    serializer_class = StudyPeriodSerializer
    permission_classes = (StudyPeriodViewSetPermission,)

    @swagger_auto_schema(operation_description='获取最新的一期青年大学习',
                         responses={200: StudyPeriodSerializer()})
    @action(methods=['GET'], detail=False)
    def lastst(self, request):
        lastst_study = StudyPeriod.objects.latest('id')
        serializer = self.get_serializer(lastst_study)
        return Response(serializer.data)


class StudyRecordingViewSet(mixins.CreateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    queryset = StudyRecording.objects.all()
    serializer_class = StudyRecordingSerializer
    # grpc_stub = api_pb2_grpc.CreditStub(
        # grpc.insecure_channel('localhost:50051'))


    @action(methods=['GET'], detail=False)
    def as_excel(self, request):
        serializer = StudyRecordingListSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data['college_id'] == -1 and not request.user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)
        elif serializer.validated_data['college_id'] != -1 and not user_has_college_permission(request.user, serializer.validated_data['college_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)
        periods = StudyPeriod.objects.filter(season=serializer.validated_data['season'])

        excel_data = []
        excel_header = ['学号', '姓名']
        for period in periods:
            excel_header.append('第%d季第%d期完成情况' % (period.season, period.period))
        excel_data.append(excel_header)

        if serializer.validated_data['college_id'] == -1:
            recordings = StudyRecording.objects.select_related('user_id').select_related('study_id').filter(study_id__in=periods).order_by('user_id')
        else:
            recordings = StudyRecording.objects.select_related('user_id').select_related('study_id').filter(user_id__college=serializer.validated_data['college_id'], study_id__in=periods).order_by('user_id')
        
        is_start_flag = 0
        excel_iter = ['未完成'] * len(excel_header)
        for r in recordings.iterator():
            if excel_iter[0] != r.user_id.id:
                if not is_start_flag:
                    is_start_flag = 1
                else:
                    excel_data.append(excel_iter)
                excel_iter = ['未完成'] * len(excel_header)
                excel_iter[0] = str(r.user_id.id)
                excel_iter[1] = r.user_id.name
            excel_iter[r.study_id.period + 2] = '已完成'
        excel_data.append(excel_iter)
            

        sheet = excel.pe.Sheet(excel_data)
        book = excel.pe.Book({'sheet1': sheet})
        return excel.make_response(book, "xlsx", file_name = "main.xlsx", sheet_name = "main")

    def create(self, request, *args, **kwargs):
        lastst_study = StudyPeriod.objects.latest('id')
        recordings = self.get_queryset().order_by('-id')
        if len(recordings) == 0:
            index = 1
            score = 1
        else:
            if recordings[0].study_id.id == lastst_study.id:
                return Response("已经学习过啦！", status=HTTP_400_BAD_REQUEST)
            index = self.get_index(recordings, lastst_study.id)
            score = min(index, 5)

        recording = StudyRecording.objects.create(
            user_id=request.user, study_id=lastst_study, score=score, detail="连续学习%d期" % index)

        # self.send_grpc(recording)

        request.user.total_score += score
        request.user.continue_study = index
        request.user.total_study += 1
        request.user.save()
        serializer = self.get_serializer(recording)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        return StudyRecording.objects.filter(user_id=self.request.user)

    # 得到连续签到次数
    def get_index(self, recordings, last_id):
        if len(recordings) == 0:
            return 1
        if last_id - recordings[0].study_id.id != 1:
            return 1
        i = 1
        while True:
            try:
                if recordings[i - 1].study_id.id - recordings[i].study_id.id != 1:
                    break
            except:
                break
            i += 1
        return i + 1

    def send_grpc(self, study_score):
        return self.grpc_stub.AddScore(api_pb2.AddScoreReq(
            user_id=str(self.request.user.id), score=study_score.score, comment="青年大学习" + study_score.detail))
