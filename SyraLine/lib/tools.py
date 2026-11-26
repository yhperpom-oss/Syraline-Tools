"""Compatibility boundary for the original 15 tool implementations.

Loads the legacy dashboard as a normal compiled package (lib.legacy) so it
works both from source and inside a Nuitka-compiled build.
"""
from .legacy import main as legacy
from .legacy import settings as legacy_settings
legacy._sound_enabled = False

from .localization import translate
_original_translate = legacy.t


def tool_translate(key, lang='fr', **kwargs):
    entries = legacy_settings.TRANSLATIONS.get(key, {})
    if lang in entries:
        return _original_translate(key, lang, **kwargs)
    return translate(_original_translate(key, 'en', **kwargs), lang)


legacy.t = tool_translate
