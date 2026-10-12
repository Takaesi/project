import string
import unittest

from password_manager.passwords import PasswordGenerator, generate_password


class GeneratePasswordTests(unittest.TestCase):
    def test_generates_requested_length_with_default_character_sets(self):
        password = PasswordGenerator(64).generate()

        self.assertEqual(len(password), 64)
        self.assertTrue(any(character in string.ascii_letters for character in password))
        self.assertTrue(any(character in string.digits for character in password))
        self.assertTrue(any(character in "!@#$%^&*()-_=+?" for character in password))

    def test_can_disable_digits_and_symbols(self):
        password = generate_password(128, digits=False, symbols=False)

        self.assertEqual(len(password), 128)
        self.assertTrue(all(character in string.ascii_letters for character in password))

    def test_generator_is_comparable_and_validates_length(self):
        self.assertEqual(PasswordGenerator(24), PasswordGenerator(24))
        self.assertNotEqual(PasswordGenerator(24), PasswordGenerator(25))
        with self.assertRaises(ValueError):
            PasswordGenerator(0)
