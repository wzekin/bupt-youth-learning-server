from django.contrib import admin

from .models import Commodity, PurchaseRecord


class PurchaseRecordAdmin(admin.ModelAdmin):
    search_fields = ["customer"]
    autocomplete_fields = ["customer"]


class CommodityAdmin(admin.ModelAdmin):
    search_fields = ["owner"]
    autocomplete_fields = ["owner"]


admin.site.register(Commodity, CommodityAdmin)
admin.site.register(PurchaseRecord, PurchaseRecordAdmin)
