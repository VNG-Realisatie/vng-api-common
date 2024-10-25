import warnings

from rest_framework.routers import APIRootView as _APIRootView
from rest_framework_nested import routers


class APIRootView(_APIRootView):
    permission_classes = ()


class NestedRegisteringMixin:
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

        if "base_name" in kwargs:
            warnings.warn(
                "base_name kwarg is deprecated, use basename instead",
                DeprecationWarning,
            )
            kwargs["basename"] = kwargs["base_name"]
            del kwargs["base_name"]

        base_name = kwargs.get("basename") or self.get_default_basename(viewset)

        self._nested_router = NestedSimpleRouter(
            self, prefix, lookup=base_name, trailing_slash=False
        )
        for _nested in nested:
            self._nested_router.register(
                _nested.prefix, _nested.viewset, _nested.nested, **_nested.kwargs
            )


class NestedSimpleRouter(NestedRegisteringMixin, routers.NestedSimpleRouter):
    pass


class DefaultRouter(NestedRegisteringMixin, routers.DefaultRouter):
    APIRootView = APIRootView


class nested:
    def __init__(self, prefix, viewset, nested=None, **kwargs):
        self.prefix = prefix
        self.viewset = viewset
        self.nested = nested
        self.kwargs = kwargs

    def __repr__(self):
        return "nested(prefix={!r}, viewset={!r}".format(self.prefix, self.viewset)
