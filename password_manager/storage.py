import base64
import json
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import KDF_ITERATIONS, SALT_SIZE, VAULT_FILE


class Vault:
    """Шифрованное ъранилище записей."""

    def __init__(self):
        self.entries = []
        self._salt = b""
        self._fernet = None

    @staticmethod
    def exists():
        return VAULT_FILE.exists()

    def _make_fernet(self, master_password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=KDF_ITERATIONS,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode("utf-8")))
        return Fernet(key)

    def create(self, master_password):
        self._salt = os.urandom(SALT_SIZE)
        self._fernet = self._make_fernet(master_password, self._salt)
        self.entries = []
        self.save()

    def unlock(self, master_password):
        """Возвращает True, если пароль верный."""
        with VAULT_FILE.open("rb") as vault_file:
            raw = vault_file.read()
        salt, token = raw[:SALT_SIZE], raw[SALT_SIZE:]
        fernet = self._make_fernet(master_password, salt)
        try:
            data = fernet.decrypt(token)
        except InvalidToken:
            return False
        self._salt, self._fernet = salt, fernet
        self.entries = json.loads(data.decode("utf-8"))
        return True

    def save(self):
        data = json.dumps(self.entries, ensure_ascii=False).encode("utf-8")
        token = self._fernet.encrypt(data)
        tmp = VAULT_FILE.with_name(VAULT_FILE.name + ".tmp")
        with tmp.open("wb") as vault_file:
            vault_file.write(self._salt + token)
        os.replace(tmp, VAULT_FILE)
