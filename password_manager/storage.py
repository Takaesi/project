import base64
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import KDF_ITERATIONS, SALT_SIZE, VAULT_FILE
from .entities import Entry, EntryCollection, Entity, FieldMap
from .json_codec import JsonCodec


class Vault(Entity):
    """Шифрованное хранилище записей."""

    def __init__(self, path=None):
        self.path = VAULT_FILE if path is None else Path(path)
        self.entries = EntryCollection()
        self._salt = b""
        self._fernet = None

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = Path(value)

    @property
    def entries(self):
        return self._entries

    @entries.setter
    def entries(self, value):
        self._entries = value if isinstance(value, EntryCollection) else EntryCollection(value)

    def identity(self):
        return str(self.path), self.entries.identity()

    def exists(self):
        return self.path.exists()

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
        self.entries = EntryCollection()
        self.save()

    def unlock(self, master_password):
        """Возвращает True, если пароль верный."""
        with self.path.open("rb") as vault_file:
            raw = vault_file.read()
        salt, token = raw[:SALT_SIZE], raw[SALT_SIZE:]
        fernet = self._make_fernet(master_password, salt)
        try:
            data = fernet.decrypt(token)
        except InvalidToken:
            return False
        stored_entries = JsonCodec.loads(data.decode("utf-8"))
        if not isinstance(stored_entries, list):
            raise ValueError("Некорректный формат хранилища")
        entries = []
        for fields in stored_entries:
            if not isinstance(fields, FieldMap):
                raise ValueError("Некорректная запись в хранилище")
            entries.append(Entry.from_fields(fields))
        self._salt, self._fernet = salt, fernet
        self.entries = EntryCollection(entries)
        return True

    def save(self):
        if self._fernet is None:
            raise RuntimeError("Хранилище не открыто")
        payload = [entry.to_fields() for entry in self.entries]
        data = JsonCodec.dumps(payload, indent=None).encode("utf-8")
        token = self._fernet.encrypt(data)
        tmp = self.path.with_name(self.path.name + ".tmp")
        with tmp.open("wb") as vault_file:
            vault_file.write(self._salt + token)
        os.replace(tmp, self.path)

    def __eq__(self, other):
        return isinstance(other, Vault) and self.identity() == other.identity()

    def __repr__(self):
        return f"Vault(path={str(self.path)!r}, entries={len(self.entries)})"

    def __str__(self):
        return f"Зашифрованное хранилище ({len(self.entries)} записей)"
