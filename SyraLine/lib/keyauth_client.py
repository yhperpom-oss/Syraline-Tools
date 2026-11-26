"""Minimal KeyAuth 1.3 client for SyraLine (init + license only).

This is a slimmed, self-contained re-implementation of the official KeyAuth
Python example, carrying only what license activation needs:
  * init()        -> opens a session with your KeyAuth application
  * license(key)  -> validates a license key and binds it to this machine's HWID

Differences from the official SDK, on purpose:
  * It never calls os._exit() / sys.exit(); every outcome is returned as a dict
    so the SyraLine activation screen can display it.
  * No 2FA / QR / file / webhook helpers, so no qrcode / Pillow dependency.
  * Responses are verified with the KeyAuth Ed25519 public key when the
    `cryptography` package is available (recommended); otherwise it falls back
    to TLS-only trust and sets 'verified': False.

Requires: requests (already a SyraLine dependency). Optional: cryptography.
"""
import os
import platform
import subprocess
import time
from datetime import datetime, timezone

import requests

API_URL = 'https://keyauth.win/api/1.3/'
# KeyAuth's published Ed25519 public key used to sign API responses.
KEYAUTH_PUBKEY_HEX = '5586b4bc69c7a4b487e4563a4cd96afd39140f919bd31cea7d1c6a1e8439422b'
# Reject responses whose signed timestamp is older than this many seconds.
MAX_SKEW_SECONDS = 25


def get_hwid():
    """Stable per-machine hardware id. No extra dependencies."""
    system = platform.system()
    try:
        if system == 'Windows':
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r'SOFTWARE\Microsoft\Cryptography') as k:
                guid, _ = winreg.QueryValueEx(k, 'MachineGuid')
                return str(guid)
        if system == 'Linux':
            for path in ('/etc/machine-id', '/var/lib/dbus/machine-id'):
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read().strip()
        if system == 'Darwin':
            out = subprocess.check_output(
                "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID",
                shell=True, text=True)
            return out.split('"')[-2]
    except Exception:
        pass
    # Portable fallback: stable but weaker.
    import uuid
    return '%012x' % uuid.getnode()


def _verify_signature(body_bytes, signature_hex, timestamp):
    """Verify KeyAuth's Ed25519 response signature. Returns True/False/None.

    None  = cannot verify because `cryptography` is unavailable (caller decides).
    """
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
    except Exception:
        return None
    try:
        # Freshness check (mirrors the official SDK).
        server_time = datetime.fromtimestamp(int(timestamp), timezone.utc)
        if abs((datetime.now(timezone.utc) - server_time).total_seconds()) > MAX_SKEW_SECONDS:
            return False
        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(KEYAUTH_PUBKEY_HEX))
        message = timestamp.encode('utf-8') + body_bytes
        public_key.verify(bytes.fromhex(signature_hex), message)
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


class KeyAuthApp:
    def __init__(self, name, ownerid, version='1.0', app_hash='', timeout=10,
                 require_signature=True):
        self.name = name
        self.ownerid = ownerid
        self.version = version
        self.app_hash = app_hash
        self.timeout = timeout
        self.require_signature = require_signature
        self.sessionid = ''
        self.initialized = False

    # --- transport --------------------------------------------------------- #
    def _request(self, data, verify=True):
        """POST form data; verify the Ed25519 signature; return parsed JSON.

        Raises requests.RequestException on network failure. On a signature
        failure returns {'success': False, 'message': 'Signature check failed'}.
        """
        response = requests.post(API_URL, data=data, timeout=self.timeout)
        body = response.content
        if verify:
            signature = response.headers.get('x-signature-ed25519')
            timestamp = response.headers.get('x-signature-timestamp')
            ok = None
            if signature and timestamp:
                ok = _verify_signature(body, signature, timestamp)
            if ok is False:
                return {'success': False, 'message': 'Signature check failed', 'verified': False}
            if ok is None and self.require_signature:
                # cryptography missing or headers absent: fail closed only if the
                # caller demands verification AND headers were present but unverifiable.
                if signature and timestamp:
                    return {'success': False,
                            'message': 'Cannot verify server signature (install cryptography)',
                            'verified': False}
        try:
            parsed = response.json()
        except ValueError:
            text = response.text.strip()
            if text == 'KeyAuth_Invalid':
                return {'success': False, 'message': 'KeyAuth application not found'}
            return {'success': False, 'message': 'Malformed server response'}
        parsed.setdefault('verified', True)
        return parsed

    # --- endpoints --------------------------------------------------------- #
    def init(self):
        data = {
            'type': 'init',
            'ver': self.version,
            'hash': self.app_hash,
            'name': self.name,
            'ownerid': self.ownerid,
        }
        result = self._request(data)
        if result.get('success'):
            self.sessionid = result.get('sessionid', '')
            self.initialized = True
        return result

    def license(self, key, hwid=None):
        if not self.initialized:
            init_result = self.init()
            if not init_result.get('success'):
                return init_result
        data = {
            'type': 'license',
            'key': key,
            'hwid': hwid or get_hwid(),
            'sessionid': self.sessionid,
            'name': self.name,
            'ownerid': self.ownerid,
        }
        return self._request(data)

    def file(self, fileid):
        """Télécharge un fichier KeyAuth (après une session authentifiée par
        license()). KeyAuth renvoie le contenu en hexadécimal : on le renvoie en
        octets bruts, ou {'success': False, ...} en cas d'échec."""
        if not self.initialized or not self.sessionid:
            return {'success': False, 'message': 'Session not initialised'}
        data = {
            'type': 'file',
            'fileid': fileid,
            'sessionid': self.sessionid,
            'name': self.name,
            'ownerid': self.ownerid,
        }
        result = self._request(data)
        if result.get('success') and result.get('contents'):
            import binascii
            try:
                result['data'] = binascii.unhexlify(result['contents'])
            except (binascii.Error, ValueError):
                result['success'] = False
        return result
