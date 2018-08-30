import datetime

import isodate
from rest_framework import fields, serializers


class DayDurationField(fields.DurationField):

    def to_internal_value(self, value):
        if isinstance(value, datetime.timedelta):
            return value
        try:
            parsed = isodate.parse_duration(str(value))
        except isodate.ISO8601Error:
            self.fail('invalid', format='[DD] [HH:[MM:]]ss[.uuuuuu]')
        else:
            assert isinstance(parsed, datetime.timedelta)
            return parsed

    def to_representation(self, value):
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
    pass


# can't declare stuff with dashes and DSO prescribes dashed key...
ValidatieFoutSerializer._declared_fields['invalid-params'] = \
    FieldValidationErrorSerializer(source='invalid_params', many=True)
