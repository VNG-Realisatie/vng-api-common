from rest_framework.routers import APIRootView as _APIRootView
from rest_framework_nested import routers


class APIRootView(_APIRootView):
    permission_classes = ()


class ZDSNestedRegisteringMixin:
    _nested_router = None

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("trailing_slash", False)
        super().__init__(*args, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        nested_router = self._nested_router
        if nested_router is not None:
            urls += nested_router.urls
        return urls

    def register(self, prefix, viewset, nested=None, *args, **kwargs):
        super().register(prefix, viewset, *args, **kwargs)

        if not nested:
            return

        base_name = kwargs.get("base_name", self.get_default_basename(viewset))

        self._nested_router = NestedSimpleRouter(
            self, prefix, lookup=base_name, trailing_slash=False
        )
        for _nested in nested:
            self._nested_router.register(
                _nested.prefix, _nested.viewset, _nested.nested, **_nested.kwargs
            )


class NestedSimpleRouter(ZDSNestedRegisteringMixin, routers.NestedSimpleRouter):
    pass


class DefaultRouter(ZDSNestedRegisteringMixin, routers.DefaultRouter):
    APIRootView = APIRootView


class nested:
    def __init__(self, prefix, viewset, nested=None, **kwargs):
        self.prefix = prefix
        self.viewset = viewset
        self.nested = nested
        self.kwargs = kwargs

    def __repr__(self):
        return "nested(prefix={!r}, viewset={!r}".format(self.prefix, self.viewset)
