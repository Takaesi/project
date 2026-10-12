import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from password_manager.storage import Vault


class VaultTests(unittest.TestCase):
    def test_create_save_and_unlock(self):
        with tempfile.TemporaryDirectory() as directory:
            vault_path = Path(directory) / "vault.bin"
            with patch("password_manager.storage.VAULT_FILE", vault_path):
                vault = Vault()
                vault.create("correct horse battery staple")
                self.assertTrue(vault_path.exists())

                vault.entries.append(
                    {
                        "site": "example.com",
                        "login": "user",
                        "password": "secret",
                        "note": "test",
                    }
                )
                vault.save()

                unlocked = Vault()
                self.assertTrue(unlocked.unlock("correct horse battery staple"))
                self.assertEqual(unlocked.entries, vault.entries)

                wrong_password_vault = Vault()
                self.assertFalse(wrong_password_vault.unlock("incorrect"))


if __name__ == "__main__":
    unittest.main()
