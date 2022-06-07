"""
Custom operations to check the db state before applying the changes.

This is needed because of the merge with stable/1.0.x and master where different
migrations perform the same schema changes and are thus conflicting.
"""
from django.core.exceptions import FieldDoesNotExist
from django.db import migrations


def check_field_exists(connection, model, field_name):
    try:
        field = model._meta.get_field(field_name)
        column_name = field.column
    except FieldDoesNotExist:
        # best effort...
        column_name = field_name
    with connection.cursor() as cursor:
        table_description = connection.introspection.get_table_description(
            cursor, model._meta.db_table
        )
        return any(col.name == column_name for col in table_description)


class RemoveField(migrations.RemoveField):
    def state_forwards(self, app_label, state):
        # normalize to dict to support both django 2.2 and 3.2
        field_names = dict(state.models[app_label, self.model_name_lower].fields).keys()
        # if it's already removed by another operation, don't do anything
        if self.name not in field_names:
            return
        super().state_forwards(app_label, state)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        from_model = from_state.apps.get_model(app_label, self.model_name)
        field_still_exists = check_field_exists(
            schema_editor.connection, from_model, self.name
        )
        if not field_still_exists:
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        to_model = from_state.apps.get_model(app_label, self.model_name)
        field_already_exists = check_field_exists(
            schema_editor.connection, to_model, self.name
        )
        if field_already_exists:
            return
        super().database_backwards(app_label, schema_editor, from_state, to_state)


class AddField(migrations.AddField):
    def state_forwards(self, app_label, state):
        # normalize to dict to support both django 2.2 and 3.2
        field_names = dict(state.models[app_label, self.model_name_lower].fields).keys()
        # if it's already added by another operation, don't do anything
        if self.name in field_names:
            return
        super().state_forwards(app_label, state)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        to_model = to_state.apps.get_model(app_label, self.model_name)
        field_already_exists = check_field_exists(
            schema_editor.connection, to_model, self.name
        )
        if field_already_exists:
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        from_model = from_state.apps.get_model(app_label, self.model_name)
        field_still_exists = check_field_exists(
            schema_editor.connection, from_model, self.name
        )
        if not field_still_exists:
            return
        super().database_backwards(app_label, schema_editor, from_state, to_state)
