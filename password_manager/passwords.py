import secrets
import string


def generate_password(length=16, digits=True, symbols=True):
    alphabet = string.ascii_letters
    if digits:
        alphabet += string.digits
    if symbols:
        alphabet += "!@#$%^&*()-_=+?"
    return "".join(secrets.choice(alphabet) for _ in range(length))
