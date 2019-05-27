from testapp.serializers import PersonSerializer


def test_partial_serializer_validation_gegevensgroep_invalid():
    serializer = PersonSerializer(data={
        "address": {
            "street": "Keizersgracht",
        }
    }, partial=True)

    assert not serializer.is_valid()


def test_partial_serializer_validation_gegevensgroep_valid():
    serializer = PersonSerializer(data={
        "address": {
            "street": "Keizersgracht",
            "number": "117"
        }
    }, partial=True)

    assert serializer.is_valid()


def test_partial_serializer_validation_gegevensgroep_valid2():
    serializer = PersonSerializer(data={
        "name": "Willy De Kooning",
    }, partial=True)

    assert serializer.is_valid()


def test_full_serializer_validation_gegevensgroep_valid():
    serializer = PersonSerializer(data={
        "name": "Willy De Kooning",
        "address": {
            "street": "Keizersgracht",
            "number": "117"
        }
    }, partial=False)

    assert serializer.is_valid()


def test_full_serializer_validation_gegevensgroep_valid2():
    serializer = PersonSerializer(data={
        "address": {
            "street": "Keizersgracht",
            "number": "117"
        }
    }, partial=False)

    assert not serializer.is_valid()


def test_full_serializer_validation_gegevensgroep_invalid():
    serializer = PersonSerializer(data={
        "name": "Willy De Kooning",
        "address": {
            "street": "Keizersgracht",
        }
    }, partial=False)

    assert not serializer.is_valid()
