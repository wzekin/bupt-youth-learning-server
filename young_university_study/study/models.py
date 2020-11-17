from django.db import models


class StudyPeriod(models.Model):
    """
      记录青年大学习期数
    """
    id = models.AutoField(primary_key=True)
    season = models.IntegerField("青年大学习季数", db_index=True)
    period = models.IntegerField("青年大学习期数", db_index=True)
    name = models.CharField("青年大学习期数名称", max_length=50)
    url = models.CharField("青年大学习视频链接", max_length=100)

    time = models.IntegerField("青年大学习视频秒数")

    created = models.DateTimeField(auto_now_add=True)


class StudyRecording(models.Model):
    """
      青年大学习学习记录
    """
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(
        "user.User", related_name="recording", null=False, on_delete=models.CASCADE)
    study_id = models.ForeignKey(
        StudyPeriod, null=False, on_delete=models.CASCADE)
    score = models.IntegerField("获得的积分")
    detail = models.CharField("说明", max_length=50)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user_id", "study_id"),)


def get_recording_num(study_min, study_max):
    return StudyPeriod.objects.filter(id__gte=study_min, id__lte=study_max).count()
