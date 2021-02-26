from django.contrib import admin

from .models import StudyPeriod, StudyRecording


class StudyRecordingAdmin(admin.ModelAdmin):
    search_fields = ["user_id"]
    autocomplete_fields = ["user_id"]


admin.site.register(StudyPeriod)
admin.site.register(StudyRecording, StudyRecordingAdmin)
