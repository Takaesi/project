import secrets
import string

from .entities import Entity


class PasswordGenerator(Entity):
    SYMBOLS = "!@#$%^&*()-_=+?"

    def __init__(self, length=16, digits=True, symbols=True):
        self.length = length
        self.digits = digits
        self.symbols = symbols

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        if not isinstance(value, int) or value < 1:
            raise ValueError("Длина пароля должна быть положительным числом")
        self._length = value

    @property
    def digits(self):
        return self._digits

    @digits.setter
    def digits(self, value):
        self._digits = bool(value)

    @property
    def symbols(self):
        return self._symbols

    @symbols.setter
    def symbols(self, value):
        self._symbols = bool(value)

    def identity(self):
        return self.length, self.digits, self.symbols

    def generate(self):
        alphabet = string.ascii_letters
        if self.digits:
            alphabet += string.digits
        if self.symbols:
            alphabet += self.SYMBOLS
        return "".join(secrets.choice(alphabet) for _ in range(self.length))

    def __eq__(self, other):
        return isinstance(other, PasswordGenerator) and self.identity() == other.identity()

    def __repr__(self):
        return (
            f"PasswordGenerator(length={self.length}, digits={self.digits}, "
            f"symbols={self.symbols})"
        )

    def __str__(self):
        return f"Генератор пароля ({self.length} символов)"


def generate_password(length=16, digits=True, symbols=True):
    """Совместимость с прежним API; новая логика находится в PasswordGenerator."""
    return PasswordGenerator(length, digits, symbols).generate()
