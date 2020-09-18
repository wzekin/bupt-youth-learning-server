from django.contrib import admin
from .models import *

class UserAdmin(admin.ModelAdmin):
    ordering = ['last_login']
    search_fields = ['id']

admin.site.register(User, UserAdmin)
admin.site.register(College)
admin.site.register(LeagueBranch)
admin.site.register(Permission)
