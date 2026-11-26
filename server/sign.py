"""HMAC signing shared by the server and (mirrored in) the client.

The canonical string MUST match SyraLine/lib/license.py::_sign exactly:
    nonce | machine_id | ok | token | expires | reason
with Python str() formatting of each field (so a bool renders as 'True'/'False').
"""
import hashlib
import hmac

FIELDS = ('nonce', 'machine_id', 'ok', 'token', 'expires', 'reason')


def sign(secret: str, fields: dict) -> str:
    canonical = '|'.join(str(fields.get(k, '')) for k in FIELDS)
    return hmac.new(secret.encode('utf-8'),
                    canonical.encode('utf-8'), hashlib.sha256).hexdigest()


def make_token(secret: str, key: str, machine_id: str) -> str:
    """Deterministic per-(key, machine) token so validate can recompute it."""
    msg = ('token:' + key + ':' + machine_id).encode('utf-8')
    return hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()
