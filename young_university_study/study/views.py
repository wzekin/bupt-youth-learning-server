import datetime

# import grpc
import django_excel as excel

# from .grpc import api_pb2_grpc, api_pb2
import jwt
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from ..user.models import User, user_has_college_permission
from .models import StudyPeriod, StudyRecording
from .serializers import (
    StudyPeriodSerializer,
    StudyRecordingListSerializer,
    StudyRecordingSerializer,
)


class StudyPeriodViewSetPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # 只有校级管理员可以创建
        if view.action == "create":
            return request.user.is_superuser
        return True

    def has_object_permission(self, request, view, obj):
        # 只有校级管理员可以删除
        if view.action == "destroy":
            return request.user.is_superuser
        return True


class StudyPeriodViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = StudyPeriod.objects.all()
    serializer_class = StudyPeriodSerializer
    permission_classes = (StudyPeriodViewSetPermission,)

    @swagger_auto_schema(
        operation_description="获取最新的一期青年大学习", responses={200: StudyPeriodSerializer()}
    )
    @action(methods=["GET"], detail=False)
    def lastst(self, request):
        lastst_study = StudyPeriod.objects.latest("id")
        serializer = self.get_serializer(lastst_study)
        return Response(serializer.data)


class StudyRecordingViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = StudyRecording.objects.all()
    serializer_class = StudyRecordingSerializer
    # grpc_stub = api_pb2_grpc.CreditStub(
    # grpc.insecure_channel('localhost:50051'))

    @action(methods=["GET", "POST"], detail=False)
    def as_excel(self, request):
        if request.method == "POST":
            serializer = StudyRecordingListSerializer(data=request.query_params)
            serializer.is_valid(raise_exception=True)
            if not request.user.is_superuser and not user_has_college_permission(
                request.user, serializer.validated_data["college_id"]
            ):
                return Response(status=status.HTTP_403_FORBIDDEN)

            college_id = serializer.validated_data["college_id"]
            study_min = serializer.validated_data["study_min"]
            study_max = serializer.validated_data["study_max"]
            encoded = jwt.encode(
                {
                    "college_id": college_id,
                    "study_min": study_min,
                    "study_max": study_max,
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
                },
                settings.SECRET_KEY,
                algorithm="HS256",
            )
            return Response(encoded, status=status.HTTP_200_OK)
        elif request.method == "GET":
            token = request.query_params.get("token", None)
            if token is None:
                return Response(status=status.HTTP_403_FORBIDDEN)

            try:
                decoded = jwt.decode(token, settings.SECRET_KEY, algorithm="HS256")
            except (jwt.ExpiredSignatureError, jwt.DecodeError):
                return Response(status=status.HTTP_403_FORBIDDEN)

            study_min = decoded["study_min"]
            study_max = decoded["study_max"]
            college_id = decoded["college_id"]

            periods = StudyPeriod.objects.filter(id__gte=study_min, id__lte=study_max)

            excel_data = []
            excel_header = ["学号", "姓名", "学院", "团支部"]
            for period in periods:
                excel_header.append("第%d季第%d期完成情况" % (period.season, period.period))
            excel_data.append(excel_header)

            users = User.objects.select_related("college").select_related(
                "league_branch"
            )

            if college_id != -1:
                users = users.filter(college=college_id)

            users = users.prefetch_related("recording")

            for user in users:
                excel_iter = ["未完成"] * len(excel_header)
                excel_iter[0] = str(user.id)
                excel_iter[1] = user.name
                excel_iter[2] = user.college.name if user.college is not None else ""
                excel_iter[3] = (
                    user.league_branch.name if user.league_branch is not None else ""
                )
                for r in user.recording.all():
                    if study_min <= r.study_id_id <= study_max:
                        excel_iter[r.study_id_id - periods[0].id + 4] = "已完成"

                excel_data.append(excel_iter)

            sheet = excel.pe.Sheet(excel_data)
            book = excel.pe.Book({"sheet1": sheet})
            return excel.make_response(
                book, "xlsx", file_name="main.xlsx", sheet_name="main"
            )

    def create(self, request, *args, **kwargs):
        lastst_study = StudyPeriod.objects.latest("id")
        recordings = self.get_queryset().order_by("-id")
        if len(recordings) == 0:
            index = 1
            score = 1
        else:
            if recordings[0].study_id.id == lastst_study.id:
                return Response("已经学习过啦！", status=HTTP_400_BAD_REQUEST)
            index = self.get_index(recordings, lastst_study.id)
            score = min(index, 5)

        recording = StudyRecording.objects.create(
            user_id=request.user,
            study_id=lastst_study,
            score=score,
            detail="连续学习%d期" % index,
        )

        # self.send_grpc(recording)

        request.user.total_score += score
        request.user.continue_study = index
        request.user.total_study += 1
        request.user.save()
        serializer = self.get_serializer(recording)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

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
            except Exception:
                break
            i += 1
        return i + 1
