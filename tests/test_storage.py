import json
import tempfile
import unittest
from pathlib import Path

from password_manager.entities import Entry
from password_manager.storage import Vault


class VaultTests(unittest.TestCase):
    def test_create_save_and_unlock(self):
        with tempfile.TemporaryDirectory() as directory:
            vault_path = Path(directory) / "vault.bin"
            vault = Vault(vault_path)
            vault.create("correct horse battery staple")
            self.assertTrue(vault_path.exists())

            entry = Entry("example.com", "user", "secret", "test")
            vault.entries.add(entry)
            vault.save()

            unlocked = Vault(vault_path)
            self.assertTrue(unlocked.unlock("correct horse battery staple"))
            self.assertEqual(unlocked.entries[0], entry)

            wrong_password_vault = Vault(vault_path)
            self.assertFalse(wrong_password_vault.unlock("incorrect"))

    def test_unlock_reads_existing_vault_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            vault_path = Path(directory) / "vault.bin"
            vault = Vault(vault_path)
            vault.create("correct horse battery staple")

            legacy_payload = (
                '[{"site":"legacy.example","login":"legacy-user",'
                '"password":"legacy-secret","note":"old format"}]'
            ).encode("utf-8")
            token = vault._fernet.encrypt(legacy_payload)
            vault_path.write_bytes(vault._salt + token)

            loaded = Vault(vault_path)
            self.assertTrue(loaded.unlock("correct horse battery staple"))
            self.assertEqual(loaded.entries[0].site, "legacy.example")
            self.assertEqual(loaded.entries[0].password, "legacy-secret")


if __name__ == "__main__":
    unittest.main()
