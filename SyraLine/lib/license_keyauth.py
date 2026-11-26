"""KeyAuth licensing backend for SyraLine.

Wraps keyauth_client (init + license) behind the same activate()/validate()
interface the activation screen uses. KeyAuth tracks the HWID binding and
expiry server-side, so "validate" is simply a fresh license check each launch.
"""
import time

import requests

from . import license_config as cfg
from . import license_state as state
from . import keyauth_client as ka


def machine_id():
    return ka.get_hwid()


def _app():
    return ka.KeyAuthApp(
        name=cfg.KEYAUTH_NAME,
        ownerid=cfg.KEYAUTH_OWNERID,
        version=cfg.KEYAUTH_VERSION,
        app_hash=cfg.KEYAUTH_APP_HASH,
        timeout=cfg.REQUEST_TIMEOUT,
        require_signature=cfg.KEYAUTH_REQUIRE_SIGNATURE,
    )


def _reason_from_message(message):
    m = (message or '').lower()
    if 'expired' in m:
        return 'expired'
    if 'not found' in m or 'invalid' in m or 'incorrect' in m:
        return 'invalid'
    if 'hwid' in m or 'already' in m or 'used' in m or 'maximum' in m:
        return 'bound'
    if 'banned' in m or 'blacklist' in m or 'paused' in m:
        return 'revoked'
    return 'invalid'


def _check(key):
    """Run a KeyAuth license check. Returns a normalized result dict."""
    key = (key or '').strip()
    if not key:
        return {'ok': False, 'reason': 'empty'}
    try:
        result = _app().license(key)
    except requests.RequestException:
        return {'ok': False, 'reason': 'offline', 'offline': True}
    except Exception:
        return {'ok': False, 'reason': 'server_error'}

    if result.get('success'):
        info = result.get('info') or {}
        subs = info.get('subscriptions') or [{}]
        expires = str(subs[0].get('expiry', subs[0].get('expires', '')))
        return {'ok': True, 'expires': expires, 'message': result.get('message', '')}

    message = result.get('message', '')
    return {'ok': False, 'reason': _reason_from_message(message), 'message': message}


def activate(key):
    result = _check(key)
    if result.get('ok'):
        state.save_state({
            'backend': 'keyauth',
            'key': (key or '').strip(),
            'expires': result.get('expires', ''),
            'machine_id': machine_id(),
            'last_online_ok': time.time(),
        })
    return result


def validate(st):
    key = st.get('key', '')
    if not key:
        return {'ok': False, 'reason': 'need_key'}
    result = _check(key)
    if result.get('ok'):
        state.mark_online_ok(st, expires=result.get('expires', st.get('expires', '')))
    return result
