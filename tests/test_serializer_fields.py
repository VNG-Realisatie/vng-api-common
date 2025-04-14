from dateutil.relativedelta import relativedelta
from rest_framework import serializers, viewsets

from vng_api_common.serializers import DurationField

VALID_DURATION_OPTIONS = [
    ("P10D", relativedelta(days=10)),
    ("P1M10D", relativedelta(months=1, days=10)),
    ("P1Y1M10D", relativedelta(years=1, months=1, days=10)),
    ("P-10D", relativedelta(days=-10)),
    ("P-1M-10D", relativedelta(months=-1, days=-10)),
    ("P-1Y-1M-10D", relativedelta(years=-1, months=-1, days=-10)),
    ("P1Y-1M10D", relativedelta(years=+1, months=-1, days=+10)),
]


class DurationSerializer(serializers.Serializer):
    duration = DurationField()


class DurationView(viewsets.ModelViewSet):
    serializer_class = DurationSerializer


def test_duration_field_valid_serialization():
    data = {"duration": ""}
    for duration in VALID_DURATION_OPTIONS:
        data["duration"] = duration[0]
        serializer = DurationSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.to_representation({"duration": duration[1]}) == data


def test_duration_field_valid_deserialization():
    data = {"duration": ""}
    for duration in VALID_DURATION_OPTIONS:
        data["duration"] = duration[0]
        serializer = DurationSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.to_internal_value(data) == {"duration": duration[1]}


def test_duration_field_invalid_deserialization():
    duration_options = [
        "test",
        "10D",
        "-P10D",
        "-P-10D",
    ]
    data = {"duration": ""}
    for d in duration_options:
        data["duration"] = d
        serializer = DurationSerializer(data=data)
        assert not serializer.is_valid()
        assert (
            serializer.errors["duration"][0]
            == "Duration has wrong format. Use one of these formats instead: P(n)Y(n)M(n)D."
        )
