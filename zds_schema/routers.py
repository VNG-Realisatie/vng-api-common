from rest_framework_nested import routers
from rest_framework_nested.routers import NestedSimpleRouter  # noqa


class DefaultRouter(routers.DefaultRouter):
    __nested_router = None

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('trailing_slash', False)
        super().__init__(*args, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        nested_router = self.__nested_router
        if nested_router is not None:
            urls += nested_router.urls
        return urls

    def register(self, prefix, viewset, nested=None, *args, **kwargs):
        base_name = kwargs.pop('base_name', self.get_default_base_name(viewset))

        super().register(prefix, viewset, *args, **kwargs)

        if not nested:
            return

        nested_router = routers.NestedSimpleRouter(
            self, prefix,
            lookup=base_name, trailing_slash=False
        )

        for _nested in nested:
            nested_router.register(_nested.prefix, _nested.viewset, **_nested.kwargs)

        self.__nested_router = nested_router


class nested:
    def __init__(self, prefix, viewset, **kwargs):
        self.prefix = prefix
        self.viewset = viewset
        self.kwargs = kwargs
