"""Garde anti-altération légère pour les builds compilés.

Ce n'est PAS un équivalent de VMProtect / Themida : juste une couche gratuite
qui refuse de s'exécuter sous un débogueur, pour gêner le crackage amateur.
Elle est totalement inactive quand on lance depuis les sources (dev).
"""
import os
import sys


def _debugger_present():
    """True si un débogueur est attaché au processus (Windows uniquement)."""
    if os.name != 'nt':
        return False
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # Débogueur local (IsDebuggerPresent) ou distant (CheckRemoteDebuggerPresent).
        if kernel32.IsDebuggerPresent():
            return True
        present = ctypes.c_int(0)
        kernel32.CheckRemoteDebuggerPresent(
            kernel32.GetCurrentProcess(), ctypes.byref(present)
        )
        return bool(present.value)
    except Exception:
        return False


def guard():
    """En build compilé, quitte silencieusement si un débogueur est détecté.
    No-op depuis les sources pour ne pas gêner le développement."""
    from .constants import FROZEN
    if not FROZEN:
        return
    try:
        if _debugger_present():
            os._exit(1)
    except Exception:
        # Une garde qui plante ne doit jamais empêcher un utilisateur légitime.
        return
