import datetime

import isodate
from rest_framework import fields


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
