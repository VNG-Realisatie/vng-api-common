from rest_framework.reverse import reverse


class APIMixin:

    def get_absolute_api_url(self, request=None, **kwargs) -> str:
        """
        Build the absolute URL of the object in the API.
        """
        # build the URL of the informatieobject
        resource_name = self._meta.model_name

        reverse_kwargs = {'uuid': self.uuid}
        reverse_kwargs.update(**kwargs)

        url = reverse(
            f'{resource_name}-detail',
            kwargs=reverse_kwargs, request=request
        )
        return url
