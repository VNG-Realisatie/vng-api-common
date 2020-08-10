from testapp.serializers import GroupSerializer
from vng_api_common.exception_handling import get_validation_errors


def test_create_invalid_params():
    """
    Test that nested validation works as expected.

    Original validation errors:

    {
        'person': [
            {
            },
            {
                'address': {
                    'street': [
                        ErrorDetail(string='This field is required.', code='required')
                    ]
                }
            }, {
                'name': [
                    ErrorDetail(string='This field is required.', code='required')
                ]
            }
        ]
    }

    Expected converted validation errors (`dict`'s are actually `OrderedDict`'s):

    [
        {
            'name': 'person.1.address.street',
            'code': 'required',
            'reason': 'This field is required.'
        }
        {
            'name': 'person.2.name',
            'code': 'required',
            'reason': 'This field is required.'
        }
    ]
    """
    serializer = GroupSerializer(
        data={
            "person": [
                {
                    "name": "john",
                    "address": {"street": "Keizersgracht", "number": "416"},
                },
                {"name": "jane", "address": {"number": "117"}},
                {"address": {"street": "Herengracht", "number": "100"}},
            ]
        },
        partial=False,
    )

    assert not serializer.is_valid()

    validation_errors = list(get_validation_errors(serializer.errors))

    assert validation_errors[0]["name"] == "person.1.address.street"
    assert validation_errors[0]["code"] == "required"

    assert validation_errors[1]["name"] == "person.2.name"
    assert validation_errors[1]["code"] == "required"


def test_create_valid():
    serializer = GroupSerializer(
        data={
            "person": [
                {
                    "name": "test",
                    "address": {"street": "Keizersgracht", "number": "117"},
                },
                {
                    "name": "test2",
                    "address": {"street": "Herengracht", "number": "100"},
                },
            ]
        },
        partial=False,
    )

    assert serializer.is_valid()
