from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VAULT_FILE = PROJECT_ROOT / "vault.bin"
SALT_SIZE = 16
KDF_ITERATIONS = 480_000
CLIPBOARD_CLEAR_MS = 20_000
