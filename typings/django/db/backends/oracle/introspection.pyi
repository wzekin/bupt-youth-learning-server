from typing import Any

from django.db.backends.base.introspection import (
    BaseDatabaseIntrospection as BaseDatabaseIntrospection,
)

FieldInfo: Any

class DatabaseIntrospection(BaseDatabaseIntrospection):
    cache_bust_counter: int = ...
    def data_types_reverse(self): ...
    def get_field_type(self, data_type: Any, description: Any): ...
    def get_table_list(self, cursor: Any): ...
    def get_table_description(self, cursor: Any, table_name: Any): ...
    def identifier_converter(self, name: Any): ...
    def get_sequences(self, cursor: Any, table_name: Any, table_fields: Any = ...): ...
    def get_relations(self, cursor: Any, table_name: Any): ...
    def get_key_columns(self, cursor: Any, table_name: Any): ...
    def get_primary_key_column(self, cursor: Any, table_name: Any): ...
    def get_constraints(self, cursor: Any, table_name: Any): ...
