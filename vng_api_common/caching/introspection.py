from rest_framework import mixins
from rest_framework.generics import GenericAPIView


def has_cache_header(view: GenericAPIView) -> bool:
    if view.request is None:
        return False

    method = view.request.method
    if method not in ("GET", "HEAD"):
        return False

    if hasattr(view, "detail") and not view.detail:
        return False

    if not isinstance(view, mixins.RetrieveModelMixin):
        return False

    conditional_retrieves = getattr(view, "_conditional_retrieves", [])
    return method == "HEAD" or view.action in conditional_retrieves
