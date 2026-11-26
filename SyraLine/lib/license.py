"""License gate for SyraLine (backend-agnostic).

On every launch, require_license() runs *before* the main UI:
  1. If a key is already stored, it is re-validated online silently. On success
     the app launches; on an explicit rejection the activation screen reopens.
  2. If the backend is unreachable but the machine validated recently, a short
     offline grace window keeps the app usable.
  3. If no valid license is stored, the activation screen asks for a key.

The active backend is chosen in license_config.BACKEND ('keyauth' or 'server').
Both expose the same interface: machine_id(), activate(key), validate(state).
"""
import os

from . import license_config as cfg
# Shared local state helpers (re-exported for the activation screen).
from .license_state import (  # noqa: F401
    LICENSE_PATH, load_state, save_state, clear_state, within_grace,
)


def _backend():
    if cfg.BACKEND == 'server':
        from . import license_server
        return license_server
    from . import license_keyauth
    return license_keyauth


def machine_id():
    return _backend().machine_id()


def activate(key):
    return _backend().activate(key)


def validate(state):
    return _backend().validate(state)


def require_license(language=None):
    """Return True if the app is allowed to launch."""
    # Dev-only bypass: honored for source runs, NEVER in a compiled release build.
    from .constants import FROZEN
    if not FROZEN and os.environ.get('SYRALINE_LICENSE_SKIP') == '1':
        return True

    state = load_state()
    if state.get('key'):
        result = validate(state)
        if result.get('ok'):
            return True
        if result.get('offline') and within_grace(state):
            return True
        reason = result.get('reason', 'invalid')
    else:
        reason = 'need_key'

    from .license_screen import LicenseGate
    return bool(LicenseGate(language=language, reason=reason,
                            prefill=state.get('key', '')).run())
