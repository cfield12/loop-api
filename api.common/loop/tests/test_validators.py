import unittest
from unittest.mock import Mock, call, patch
from uuid import UUID

from loop.api_classes.validators import (
    validate_code,
    validate_email_address,
    validate_int_thresholds,
    validate_str_uuid,
)

TEST_UUID = '86125274-40a1-70ec-da28-f779360f7c07'


class TestValidators(unittest.TestCase):
    def test_validate_uuid(self):
        uuid = validate_str_uuid(TEST_UUID)
        self.assertIsInstance(uuid, UUID)
        self.assertEqual(uuid.version, 4)

    def test_validate_uuid_not_a_uuid(self):
        self.assertRaises(ValueError, validate_str_uuid, 'not a uuid')

    def test_validate_uuid_type_error(self):
        self.assertRaises(TypeError, validate_str_uuid, 55)

    def test_validate_uuid_type_error_uuid_version(self):
        self.assertRaises(TypeError, validate_str_uuid, TEST_UUID, version=4)

    def test_validate_code(self):
        code = validate_code('123456')
        self.assertEqual(code, '123456')

    def test_validate_code_not_digit(self):
        self.assertRaises(ValueError, validate_code, '1234f6')

    def test_validate_code_not_right_length(self):
        self.assertRaises(ValueError, validate_code, '1234567')

    def test_validate_email_address(self):
        email = validate_email_address('hello@test-email.com')
        self.assertEqual(email, 'hello@test-email.com')

    def test_validate_email_address_invalid(self):
        self.assertRaises(ValueError, validate_email_address, 'test-email.com')

    def test_validate_int_thresholds(self):
        number = 3
        response = validate_int_thresholds(number)
        self.assertEqual(response, number)

    def test_validate_int_thresholds_too_small(self):
        self.assertRaises(ValueError, validate_int_thresholds, 0)

    def test_validate_int_thresholds_too_big(self):
        self.assertRaises(ValueError, validate_int_thresholds, 6)


if __name__ == '__main__':
    unittest.main()
