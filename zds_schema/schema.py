from drf_yasg.inspectors import SwaggerAutoSchema


class AutoSchema(SwaggerAutoSchema):

    @property
    def model(self):
        qs = self.view.get_queryset()
        return qs.model

    def get_operation_id(self, operation_keys):
        """
        Simply return the model name as lowercase string, postfixed with the operation name.
        """
        action = operation_keys[-1]
        model_name = self.model._meta.model_name
        return f"{model_name}_{action}"

    def get_request_serializer(self):
        if hasattr(self.view, 'action'):
            action = getattr(self.view, self.view.action)
            if getattr(action, 'is_search_action', False):
                return self.view.get_search_input_serializer_class()()
        return super().get_request_serializer()
