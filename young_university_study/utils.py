from django.conf import settings
from hashids import Hashids


def get_Hashids() -> Hashids:
    return Hashids(
        salt=settings.SECRET_KEY,
        min_length=6,
        alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ23456789",
    )
