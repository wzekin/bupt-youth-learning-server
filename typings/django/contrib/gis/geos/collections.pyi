from typing import Any

from django.contrib.gis.geos.geometry import (
    GEOSGeometry as GEOSGeometry,
    LinearGeometryMixin as LinearGeometryMixin,
)

class GeometryCollection(GEOSGeometry):
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def __iter__(self) -> Any: ...
    def __len__(self): ...
    @property
    def kml(self): ...
    @property
    def tuple(self): ...
    coords: Any = ...

class MultiPoint(GeometryCollection): ...
class MultiLineString(LinearGeometryMixin, GeometryCollection): ...
class MultiPolygon(GeometryCollection): ...