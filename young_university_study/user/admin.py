from django.contrib import admin

from .models import *


class UserAdmin(admin.ModelAdmin):
    ordering = ['last_login']
    search_fields = ['id']
    autocomplete_fields = ["college", "league_branch"]


class CollegeAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']


class LeagueBranchAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']


class PermissionAdmin(admin.ModelAdmin):
    ordering = ['id']
    autocomplete_fields = ["user_id"]


admin.site.register(User, UserAdmin)
admin.site.register(College, CollegeAdmin)
admin.site.register(LeagueBranch, LeagueBranchAdmin)
admin.site.register(Permission, PermissionAdmin)
