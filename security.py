"""Password verification helpers. Credentials live only in Streamlit secrets."""
import hashlib
import hmac
import secrets

ITERATIONS = 600_000


def make_hash(password: str, salt: bytes | None = None) -> str:
    if len(password) < 12:
        raise ValueError('Password must be at least 12 characters.')
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}'


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt_hex, digest_hex = encoded.split('$')
        if scheme != 'pbkdf2_sha256' or int(iterations) < 100_000:
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(actual, bytes.fromhex(digest_hex))
    except (ValueError, TypeError, AttributeError):
        return False
