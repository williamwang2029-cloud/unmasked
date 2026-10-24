import hashlib, hmac, os
from pathlib import Path
import pandas as pd
from cryptography.fernet import Fernet

KEYS_DIR = Path("keys")

def ensure_keys(keys_dir="keys"):
    global KEYS_DIR
    KEYS_DIR = Path(keys_dir)
    KEYS_DIR.mkdir(exist_ok=True)
    vk = KEYS_DIR / "vault.key"
    if not vk.exists():
        vk.write_bytes(Fernet.generate_key())
    jk = KEYS_DIR / "join.key"
    if not os.environ.get("JOIN_KEY") and not jk.exists():
        jk.write_bytes(os.urandom(32).hex().encode())

def _join_key():
    k = os.environ.get("JOIN_KEY")
    if k:
        return k.encode()
    ensure_keys(KEYS_DIR)
    return (KEYS_DIR / "join.key").read_bytes()

def _vault():
    ensure_keys(KEYS_DIR)
    return Fernet((KEYS_DIR / "vault.key").read_bytes())

def join_token(value):
    return hmac.new(_join_key(), str(value).encode(), hashlib.sha256).hexdigest()[:16]

def _vault_path(col):
    return str(KEYS_DIR / f"vault_{col}.csv")

def tokenize_column(df, col, vault_path=None):
    """Replace `col` with deterministic HMAC tokens. Originals are Fernet-encrypted into a
    per-column vault file (keys/vault_<col>.csv). The vault key lives in keys/vault.key."""
    vault_path = vault_path or _vault_path(col)
    f = _vault()
    values = df[col].astype(str)
    tokens = values.map(join_token)
    vault = pd.DataFrame({"token": tokens, "encrypted_value": values.map(lambda v: f.encrypt(v.encode()).decode())}).drop_duplicates("token")
    Path(vault_path).parent.mkdir(exist_ok=True)
    vault.to_csv(vault_path, index=False)
    out = df.copy()
    out[col] = tokens
    return out

def detokenize(token, col, vault_path=None):
    vault = pd.read_csv(vault_path or _vault_path(col))
    enc = vault.loc[vault["token"] == token, "encrypted_value"]
    if enc.empty:
        raise KeyError("token not found")
    return _vault().decrypt(enc.iloc[0].encode()).decode()
