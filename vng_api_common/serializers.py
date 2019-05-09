import datetime
from collections import OrderedDict

from django.db import transaction

import isodate
from djchoices import DjangoChoices
from rest_framework import fields, serializers

from .descriptors import GegevensGroepType

try:
    from relativedeltafield import format_relativedelta, relativedelta
except ImportError:
    format_relativedelta = None
    relativedelta = None


class DurationField(fields.DurationField):

    def to_internal_value(self, value):
        if isinstance(value, datetime.timedelta):
            return value
        try:
            parsed = isodate.parse_duration(str(value))
        except isodate.ISO8601Error:
            self.fail('invalid', format='P(n)Y(n)M(n)D')
        else:
            if isinstance(parsed, isodate.Duration):
                # TODO: start should probably be a proper object, but we should
                # really switch to relativedeltafield
                parsed = parsed.totimedelta(start=datetime.datetime.now())
            assert isinstance(parsed, datetime.timedelta)
            return parsed

    def to_representation(self, value):
        if relativedelta and isinstance(value, relativedelta):
            return format_relativedelta(value)

        return isodate.duration_isoformat(value)


class FieldValidationErrorSerializer(serializers.Serializer):
    """
    Formaat van validatiefouten.
    """
    name = serializers.CharField(help_text="Naam van het veld met ongeldige gegevens")
    code = serializers.CharField(help_text="Systeemcode die het type fout aangeeft")
    reason = serializers.CharField(help_text="Uitleg wat er precies fout is met de gegevens")


class FoutSerializer(serializers.Serializer):
    """
    Formaat van HTTP 4xx en 5xx fouten.
    """
    type = serializers.CharField(
        help_text="URI referentie naar het type fout, bedoeld voor developers",
        required=False, allow_blank=True
    )
    # not according to DSO, but possible for programmatic checking
    code = serializers.CharField(help_text="Systeemcode die het type fout aangeeft")
    title = serializers.CharField(help_text="Generieke titel voor het type fout")
    status = serializers.IntegerField(help_text="De HTTP status code")
    detail = serializers.CharField(help_text="Extra informatie bij de fout, indien beschikbaar")
    instance = serializers.CharField(
        help_text="URI met referentie naar dit specifiek voorkomen van de fout. Deze kan "
                  "gebruikt worden in combinatie met server logs, bijvoorbeeld."
    )


class ValidatieFoutSerializer(FoutSerializer):
    invalid_params = FieldValidationErrorSerializer(many=True)


def add_choice_values_help_text(choices: DjangoChoices) -> str:
    displays = "\n".join([
        f"* `{value}` - {display}"
        for value, display in choices.choices
    ])
    return f"De mapping van waarden naar weergave is als volgt:\n\n{displays}"


class GegevensGroepSerializerMetaclass(serializers.SerializerMetaclass):

    def __new__(cls, name, bases, attrs):
        Meta = attrs.get('Meta')
        if Meta:
            assert hasattr(Meta, 'model'), "The 'model' class must be defined on the Meta."
            assert hasattr(Meta, 'gegevensgroep'), "The 'gegevensgroep' name must be defined on the Meta."

            gegevensgroep = getattr(Meta.model, Meta.gegevensgroep)
            Meta.fields = []

            extra_kwargs = {}

            for field_name, model_field in gegevensgroep.mapping.items():
                Meta.fields.append(field_name)

                # the field is always required and may not be empty in any form
                default_extra_kwargs = {
                    'source': model_field.name,
                    'required': field_name not in gegevensgroep.optional,
                    'allow_null': False,
                    'allow_blank': field_name in gegevensgroep.optional,
                }

                internal_type = model_field.get_internal_type()
                if internal_type not in ['CharField', 'TextField']:
                    del default_extra_kwargs['allow_blank']
                if internal_type == 'BooleanField':
                    del default_extra_kwargs['allow_null']

                # if internal_type == 'RelativeDeltaField':
                #     import bpdb; bpdb.set_trace()

                extra_kwargs[field_name] = default_extra_kwargs

                declared_extra_kwargs = getattr(Meta, 'extra_kwargs', {}).get(field_name)
                if declared_extra_kwargs:
                    extra_kwargs[field_name].update(declared_extra_kwargs)

            Meta.extra_kwargs = extra_kwargs

        return super().__new__(cls, name, bases, attrs)


class GegevensGroepSerializer(serializers.ModelSerializer, metaclass=GegevensGroepSerializerMetaclass):
    """
    Generate a serializer out of a GegevensGroepType.

    Usage::

    >>> class VerlengingSerializer(GegevensGroepSerializer):
    ...     class Meta:
    ...         model = Zaak
    ...         gegevensgroep = 'verlenging'
    >>>

    Where ``Zaak.verlenging`` is a :class:``GegevensGroepType``.
    """

    def to_representation(self, instance) -> dict:
        """
        Output the result of accessing the descriptor.
        """
        ret = OrderedDict()
        fields = self._readable_fields

        for field in fields:
            attribute = instance[field.field_name]
            if attribute is None:
                ret[field.field_name] = None
            else:
                ret[field.field_name] = field.to_representation(attribute)
        return ret

    def to_internal_value(self, data):
        """
        Pass through the original keys instead of reverse-mapping the source attrs.
        """
        value = super().to_internal_value(data)
        ret = {}
        for name, field in self.fields.items():
            if field not in self._writable_fields:
                continue
            if field.source not in value:
                continue
            ret[name] = value[field.source]
        return ret


class NestedGegevensGroepMixin:
    """
    Set gegevensgroepdata from validated nested data.

    Usage: include the mixin on the ModelSerializer that has gegevensgroepen.
    """

    def _is_gegevensgroep(self, name: str):
        attr = getattr(self.Meta.model, name)
        return isinstance(attr, GegevensGroepType)

    @transaction.atomic
    def create(self, validated_data):
        """
        Handle nested writes.
        """
        gegevensgroepen = {}

        for name in list(validated_data.keys()):
            if not self._is_gegevensgroep(name):
                continue

            gegevensgroepen[name] = validated_data.pop(name)

        # perform the default create
        obj = super().create(validated_data)

        for name, gegevensgroepdata in gegevensgroepen.items():
            setattr(obj, name, gegevensgroepdata)

        obj.save()

        return obj

    def update(self, instance, validated_data):
        """
        Handle nested writes.
        """
        for name in list(validated_data.keys()):
            if not self._is_gegevensgroep(name):
                continue
            setattr(instance, name, validated_data.pop(name))
        return super().update(instance, validated_data)
