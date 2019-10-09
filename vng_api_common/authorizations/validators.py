from typing import List

from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import ErrorDetail
from rest_framework.serializers import ValidationError

from ..constants import ComponentTypes
from ..utils import underscore_to_camel
from .models import Applicatie


class UniqueClientIDValidator:
    code = "clientId-exists"
    message = _(
        "The clientID(s) {client_id} are already used in application(s) {app_id}"
    )

    def set_context(self, serializer_field):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # Determine the existing instance, if this is an update operation.
        self.instance = getattr(serializer_field.parent, "instance", None)

    def __call__(self, value: List[str]):
        qs = Applicatie.objects.all()

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        existing = qs.filter(client_ids__overlap=value).values_list(
            "uuid", "client_ids"
        )
        if existing:
            client_ids = set()
            for _existing in existing:
                client_ids = client_ids.union(_existing[1])

            raise ValidationError(
                self.message.format(
                    client_id=", ".join(client_ids.intersection(set(value))),
                    app_id=", ".join([str(_existing[0]) for _existing in existing]),
                ),
                code=self.code,
            )


class AutorisatieValidator:
    message = _("This field is required if `component` is {component}")
    code = "required"

    REQUIRED_FIELDS_PER_COMPONENT = {
        ComponentTypes.zrc: ("max_vertrouwelijkheidaanduiding", "zaaktype"),
        ComponentTypes.drc: ("max_vertrouwelijkheidaanduiding", "informatieobjecttype"),
        ComponentTypes.brc: ("besluittype",),
    }
    MAIN_RESOURCES_FOR_COMPONENTS = {
        ComponentTypes.zrc: "zaken",
        ComponentTypes.drc: "documenten",
        ComponentTypes.brc: "besluiten",
    }

    def __call__(self, autorisatie: dict) -> None:
        component = autorisatie["component"]

        if component not in self.REQUIRED_FIELDS_PER_COMPONENT:
            return

        prefix = self.MAIN_RESOURCES_FOR_COMPONENTS[component]
        if not any(scope.startswith(f"{prefix}.") for scope in autorisatie["scopes"]):
            return

        error_dict = {}
        for field_name in self.REQUIRED_FIELDS_PER_COMPONENT[component]:
            if not autorisatie[field_name]:
                error_dict.update(
                    {
                        field_name: ErrorDetail(
                            self.message.format(
                                fields=underscore_to_camel(field_name),
                                component=component,
                            ),
                            self.code,
                        )
                    }
                )

        if error_dict:
            raise ValidationError(error_dict)
