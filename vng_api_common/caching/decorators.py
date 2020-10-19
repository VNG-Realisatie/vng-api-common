from functools import partial

from rest_framework_condition.decorators import condition as drf_condition

from .etags import etag_func


def conditional_retrieve(action="retrieve", etag_field="_etag"):
    """
    Decorate a viewset to apply conditional GET requests.
    """

    def decorator(viewset: type):
        condition = drf_condition(etag_func=partial(etag_func, etag_field=etag_field))
        original_handler = getattr(viewset, action)
        handler = condition(original_handler)
        setattr(viewset, action, handler)
        if not hasattr(viewset, "_conditional_retrieves"):
            viewset._conditional_retrieves = []
        viewset._conditional_retrieves.append(action)
        return viewset

    return decorator
