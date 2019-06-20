from testapp.serializers import GroupSerializer, PersonSerializer

from vng_api_common.exception_handling import get_validation_errors


def test_create_invalid_params():
    serializer = GroupSerializer(data={
        "person": [
            {
                "name": "test",
                "address": {
                    "number": "117"
                }
            },
            {
                "address": {
                    "street": "Herengracht",
                    "number": "100"
                }
            }
        ]
    }, partial=False)

    assert not serializer.is_valid()

    validation_errors = list(get_validation_errors(serializer.errors))

    assert validation_errors[0]['name'] == 'person.0.address.street'
    assert validation_errors[0]['code'] == 'required'

    assert validation_errors[1]['name'] == 'person.1.name'
    assert validation_errors[1]['code'] == 'required'

def test_create_valid():
    serializer = GroupSerializer(data={
        "person": [
            {
                "name": "test",
                "address": {
                    "street": "Keizersgracht",
                    "number": "117"
                }
            },
            {
                "name": "test2",
                "address": {
                    "street": "Herengracht",
                    "number": "100"
                }
            }
        ]
    }, partial=False)

    assert serializer.is_valid()
