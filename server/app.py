"""SyraLine license server (FastAPI).

Run:
    pip install -r requirements.txt
    set LICENSE_SECRET=... ADMIN_TOKEN=...   (PowerShell: $env:LICENSE_SECRET=...)
    uvicorn app:app --host 0.0.0.0 --port 8000

Public endpoints (called by the SyraLine client):
    POST /api/activate   bind a key to a machine, return a signed token
    POST /api/validate   re-check an existing key+token+machine
    GET  /health

Admin endpoints (require header  X-Admin-Token: <ADMIN_TOKEN>):
    POST   /admin/keys           create one or more keys
    GET    /admin/keys           list keys with activation counts
    POST   /admin/keys/{key}/revoke
    POST   /admin/keys/{key}/restore

LICENSE_SECRET must be identical to the client's SYRALINE_LICENSE_SECRET.
"""
import os
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

import db
import sign
import keygen

SECRET = os.environ.get('LICENSE_SECRET', 'change-me-shared-secret-please')
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '')

app = FastAPI(title='SyraLine License Server', version='1.0.0')


@app.on_event('startup')
def _startup():
    db.init_db()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _iso(ts):
    if not ts:
        return ''
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d')


def _signed(nonce, machine_id, ok, token='', expires='', reason=''):
    msg = {'nonce': nonce, 'machine_id': machine_id, 'ok': ok,
           'token': token, 'expires': expires, 'reason': reason}
    msg['sig'] = sign.sign(SECRET, msg)
    return msg


def _key_problem(record):
    """Return a reason string if the key cannot be used, else ''."""
    if record is None:
        return 'unknown_key'
    if record['status'] != 'active':
        return 'revoked'
    if record['expires_at'] and time.time() > record['expires_at']:
        return 'expired'
    return ''


def _require_admin(token):
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail='invalid admin token')


# --------------------------------------------------------------------------- #
# Public models + endpoints
# --------------------------------------------------------------------------- #
class ActivateIn(BaseModel):
    nonce: str
    key: str
    machine_id: str
    product: str = ''
    version: str = ''


class ValidateIn(BaseModel):
    nonce: str
    key: str
    token: str
    machine_id: str
    product: str = ''
    version: str = ''


@app.get('/health')
def health():
    return {'ok': True, 'service': 'syraline-license', 'time': _iso(time.time())}


@app.post('/api/activate')
def activate(body: ActivateIn):
    record = db.get_key(body.key)
    problem = _key_problem(record)
    if problem:
        return _signed(body.nonce, body.machine_id, False, reason=problem)

    already = db.get_activation(body.key, body.machine_id) is not None
    if not already and db.count_activations(body.key) >= record['max_activations']:
        return _signed(body.nonce, body.machine_id, False, reason='bound')

    token = sign.make_token(SECRET, body.key, body.machine_id)
    db.upsert_activation(body.key, body.machine_id, token)
    return _signed(body.nonce, body.machine_id, True,
                   token=token, expires=_iso(record['expires_at']))


@app.post('/api/validate')
def validate(body: ValidateIn):
    record = db.get_key(body.key)
    problem = _key_problem(record)
    if problem:
        return _signed(body.nonce, body.machine_id, False, reason=problem)

    activation = db.get_activation(body.key, body.machine_id)
    expected = sign.make_token(SECRET, body.key, body.machine_id)
    if activation is None or body.token != expected or activation['token'] != expected:
        return _signed(body.nonce, body.machine_id, False, reason='invalid')

    db.touch_activation(body.key, body.machine_id)
    return _signed(body.nonce, body.machine_id, True,
                   token=expected, expires=_iso(record['expires_at']))


# --------------------------------------------------------------------------- #
# Admin models + endpoints
# --------------------------------------------------------------------------- #
class CreateKeysIn(BaseModel):
    count: int = 1
    max_activations: int = 1
    expires_days: int = 0        # 0 = never
    note: str = ''


@app.post('/admin/keys')
def admin_create(body: CreateKeysIn, x_admin_token: str = Header(default='')):
    _require_admin(x_admin_token)
    count = max(1, min(body.count, 1000))
    expires_at = time.time() + body.expires_days * 86400 if body.expires_days > 0 else 0.0
    created = []
    for _ in range(count):
        key = keygen.new_key()
        db.add_key(key, max_activations=body.max_activations,
                   expires_at=expires_at, note=body.note)
        created.append(key)
    return {'ok': True, 'created': created, 'expires': _iso(expires_at)}


@app.get('/admin/keys')
def admin_list(x_admin_token: str = Header(default='')):
    _require_admin(x_admin_token)
    keys = []
    for k in db.list_keys():
        keys.append({
            'key': k['key'], 'status': k['status'],
            'max_activations': k['max_activations'], 'activations': k['activations'],
            'expires': _iso(k['expires_at']), 'note': k['note'],
            'created': _iso(k['created_at']),
        })
    return {'ok': True, 'keys': keys}


@app.post('/admin/keys/{key}/revoke')
def admin_revoke(key: str, x_admin_token: str = Header(default='')):
    _require_admin(x_admin_token)
    return {'ok': db.set_status(key, 'revoked')}


@app.post('/admin/keys/{key}/restore')
def admin_restore(key: str, x_admin_token: str = Header(default='')):
    _require_admin(x_admin_token)
    return {'ok': db.set_status(key, 'active')}
