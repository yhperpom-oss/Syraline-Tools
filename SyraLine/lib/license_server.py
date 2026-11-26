"""Custom-server licensing backend for SyraLine (the FastAPI server in ../server).

Signed-response protocol: the client sends a nonce; the server echoes it and
signs the security-relevant fields with a shared HMAC secret, so a spoofed
endpoint cannot forge an 'ok'. This is a deterrent, not DRM -- the secret ships
in the client.
"""
import hashlib
import hmac
import json
import os
import platform
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import license_config as cfg
from . import license_state as state
from .version import VERSION


def machine_id():
    raw = '|'.join([
        platform.node(), platform.system(), platform.machine(),
        str(uuid.getnode()),
        os.environ.get('USERNAME', os.environ.get('USER', '')),
    ])
    return hashlib.sha256(raw.encode('utf-8', 'replace')).hexdigest()[:32]


def _sign(fields):
    canonical = '|'.join(str(fields.get(k, '')) for k in
                         ('nonce', 'machine_id', 'ok', 'token', 'expires', 'reason'))
    return hmac.new(cfg.LICENSE_SECRET.encode('utf-8'),
                    canonical.encode('utf-8'), hashlib.sha256).hexdigest()


def _post(path, payload):
    url = cfg.LICENSE_API_BASE + path
    body = json.dumps(payload).encode('utf-8')
    request = Request(url, data=body, method='POST', headers={
        'Content-Type': 'application/json',
        'User-Agent': 'SyraLine/' + VERSION,
    })
    with urlopen(request, timeout=cfg.REQUEST_TIMEOUT) as response:
        data = response.read(8193)
    if len(data) > 8192:
        raise ValueError('License response too large')
    message = json.loads(data)
    if not isinstance(message, dict):
        raise ValueError('Malformed license response')
    if message.get('nonce') != payload.get('nonce'):
        return {'ok': False, 'reason': 'bad_nonce'}
    if not hmac.compare_digest(_sign(message), str(message.get('sig', ''))):
        return {'ok': False, 'reason': 'bad_signature'}
    if message.get('machine_id') not in ('', payload.get('machine_id')):
        return {'ok': False, 'reason': 'wrong_machine'}
    return message


def _nonce():
    return uuid.uuid4().hex


def activate(key):
    key = (key or '').strip()
    if not key:
        return {'ok': False, 'reason': 'empty'}
    payload = {'nonce': _nonce(), 'key': key, 'machine_id': machine_id(),
               'product': cfg.PRODUCT_ID, 'version': VERSION}
    try:
        res = _post('/api/activate', payload)
    except (URLError, HTTPError):
        return {'ok': False, 'reason': 'offline', 'offline': True}
    except (ValueError, OSError):
        return {'ok': False, 'reason': 'server_error'}
    if res.get('ok'):
        state.save_state({
            'backend': 'server', 'key': key, 'token': res.get('token', ''),
            'expires': res.get('expires', ''), 'machine_id': machine_id(),
            'last_online_ok': time.time(),
        })
    return res


def validate(st):
    key = st.get('key', '')
    token = st.get('token', '')
    if not key or not token:
        return {'ok': False, 'reason': 'need_key'}
    payload = {'nonce': _nonce(), 'key': key, 'token': token, 'machine_id': machine_id(),
               'product': cfg.PRODUCT_ID, 'version': VERSION}
    try:
        res = _post('/api/validate', payload)
    except (URLError, HTTPError):
        return {'ok': False, 'reason': 'offline', 'offline': True}
    except (ValueError, OSError):
        return {'ok': False, 'reason': 'server_error'}
    if res.get('ok'):
        state.mark_online_ok(st, expires=res.get('expires', st.get('expires', '')))
    return res
