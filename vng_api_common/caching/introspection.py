from rest_framework import mixins
from rest_framework.generics import GenericAPIView


def has_cache_header(view: GenericAPIView) -> bool:
    request = getattr(view, "request", None)
    method = getattr(view, "method", None) or request.method if request else None
    action = getattr(view, "action", None)

    if method not in ("GET", "HEAD") and action not in (
        "retrieve",
        "headers",
    ):
        return False

    if hasattr(view, "detail") and not view.detail:
        return False

    if not isinstance(view, mixins.RetrieveModelMixin):
        return False

    conditional_retrieves = getattr(view, "_conditional_retrieves", [])
    return method == "HEAD" or view.action in conditional_retrieves
