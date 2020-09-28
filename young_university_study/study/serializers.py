from rest_framework import serializers

from .models import *


class StudyPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyPeriod
        fields = '__all__'
        read_only_fields = ('id',)



class StudyRecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyRecording
        fields = '__all__'
        read_only_fields = ('id', 'create', 'user_id', 'study_id', 'score', 'detail')

class StudyRecordingListSerializer(serializers.Serializer):
    college_id = serializers.IntegerField()
    study_min = serializers.IntegerField()
    study_max = serializers.IntegerField()