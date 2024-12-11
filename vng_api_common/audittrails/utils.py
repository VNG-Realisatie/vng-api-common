import inspect
import logging

from django.apps import apps

from rest_framework import viewsets

logger = logging.getLogger(__name__)


AUDIT_TRAIL_ENABLED = apps.is_installed("vng_api_common.audittrails")


def _view_supports_audittrail(view: viewsets.ViewSet) -> bool:
    # moved from vng_api_common.inspectors
    if not AUDIT_TRAIL_ENABLED:
        return False

    if not hasattr(view, "action"):
        logger.debug("Could not determine view action for view %r", view)
        return False

    # local imports, since you get errors if you try to import non-installed app
    # models
    from vng_api_common.audittrails.viewsets import AuditTrailMixin

    relevant_bases = [
        base for base in view.__class__.__bases__ if issubclass(base, AuditTrailMixin)
    ]
    if not relevant_bases:
        return False

    # check if the view action is listed in any of the audit trail mixins
    action = view.action
    if action == "partial_update":  # partial update is self.update(partial=True)
        action = "update"

    # if the current view action is not provided by any of the audit trail
    # related bases, then it's not audit trail enabled
    action_in_audit_bases = any(
        action in dict(inspect.getmembers(base)) for base in relevant_bases
    )

    return action_in_audit_bases
