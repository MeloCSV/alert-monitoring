import pytest

from alert_monitoring.api.application.exceptions.unprocessable_entity import UnprocessableEntityException


def test_unprocessable_entity_exception_stores_message():
    expected_message = "The entity could not be processed due to invalid data."

    with pytest.raises(UnprocessableEntityException) as exception_info:
        raise UnprocessableEntityException(msg=expected_message)

    assert exception_info.value.msg == expected_message

    assert str(exception_info.value) == expected_message