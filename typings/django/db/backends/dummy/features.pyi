from django.db.backends.base.features import (
    BaseDatabaseFeatures as BaseDatabaseFeatures,
)

class DummyDatabaseFeatures(BaseDatabaseFeatures):
    supports_transactions: bool = ...
    uses_savepoints: bool = ...
