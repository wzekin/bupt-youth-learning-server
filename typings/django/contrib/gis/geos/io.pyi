from typing import Any

from django.contrib.gis.geos.prototypes.io import (  # noqa: F401
    WKBWriter as WKBWriter,
    WKTWriter as WKTWriter,
    _WKBReader,
    _WKTReader,
)

class WKBReader(_WKBReader):
    def read(self, wkb: Any): ...

class WKTReader(_WKTReader):
    def read(self, wkt: Any): ...
