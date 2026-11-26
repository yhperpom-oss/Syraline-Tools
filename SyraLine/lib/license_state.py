"""Shared local license state, used by every licensing backend."""
import json
import time

from . import license_config as cfg
from .config import PROFILE_PATH

LICENSE_PATH = PROFILE_PATH.with_name('license.json')


def load_state():
    try:
        data = json.loads(LICENSE_PATH.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(state):
    try:
        LICENSE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = LICENSE_PATH.with_suffix('.tmp')
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp.replace(LICENSE_PATH)
    except OSError:
        pass


def clear_state():
    try:
        LICENSE_PATH.unlink()
    except OSError:
        pass


def mark_online_ok(state, **extra):
    state['last_online_ok'] = time.time()
    state.update(extra)
    save_state(state)
    return state


def within_grace(state):
    last = state.get('last_online_ok')
    if not isinstance(last, (int, float)):
        return False
    return (time.time() - last) <= cfg.OFFLINE_GRACE_DAYS * 86400


def key_expired(state):
    """True si la clé mémorisée a une date d'expiration déjà dépassée.
    'expires' vide ou '0' = clé à vie (jamais expirée)."""
    raw = str(state.get('expires', '')).strip()
    if raw in ('', '0'):
        return False
    try:
        return time.time() >= float(raw)
    except (ValueError, TypeError):
        return False


def same_machine(state):
    """Anti-partage : True seulement si l'état de licence a été créé sur CETTE
    machine. Empêche de copier license.json d'un PC à un autre pour partager un
    accès VIP. (Le HWID KeyAuth reverrouille de toute façon côté serveur.)"""
    stored = state.get('machine_id')
    if not stored:
        return True  # ancien état sans HWID : toléré, le serveur revérifie
    try:
        from . import license as _license
        return str(stored) == str(_license.machine_id())
    except Exception:
        return True
