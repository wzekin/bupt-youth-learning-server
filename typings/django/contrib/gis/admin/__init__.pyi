from django.contrib.admin import (
    HORIZONTAL as HORIZONTAL,
    VERTICAL as VERTICAL,
    AdminSite as AdminSite,
    ModelAdmin as ModelAdmin,
    StackedInline as StackedInline,
    TabularInline as TabularInline,
    autodiscover as autodiscover,
    register as register,
    site as site,
)
from django.contrib.gis.admin.options import (
    GeoModelAdmin as GeoModelAdmin,
    OSMGeoAdmin as OSMGeoAdmin,
)
