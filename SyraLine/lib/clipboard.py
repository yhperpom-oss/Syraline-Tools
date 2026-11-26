"""Read the system clipboard as text (Windows-first, no dependencies).

Used so users can paste a license key into fields even in terminals that do
not support bracketed paste (e.g. classic cmd.exe), where Ctrl+V/right-click
would otherwise do nothing inside the TUI.
"""
import sys


def read_clipboard():
    try:
        if sys.platform == 'win32':
            text = _win_clipboard()
            if text:
                return text
    except Exception:
        pass
    try:
        import subprocess
        flags = 0x08000000 if sys.platform == 'win32' else 0  # CREATE_NO_WINDOW
        out = subprocess.run(
            ['powershell', '-NoProfile', '-Command', 'Get-Clipboard'],
            capture_output=True, text=True, timeout=5, creationflags=flags,
        )
        return (out.stdout or '').rstrip('\r\n')
    except Exception:
        return ''


def _win_clipboard():
    import ctypes
    CF_UNICODETEXT = 13
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    if not user32.OpenClipboard(0):
        return ''
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return ''
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            return ''
        try:
            return ctypes.c_wchar_p(pointer).value or ''
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()
