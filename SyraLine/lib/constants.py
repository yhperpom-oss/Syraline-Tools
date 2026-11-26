"""Project paths, independent of the working directory."""
import os
import sys
from pathlib import Path
APP_DIR=Path(__file__).resolve().parents[1]

def _is_frozen():
    """True when running as a compiled build (Nuitka sets __compiled__; PyInstaller sets sys.frozen)."""
    return bool(getattr(sys,'frozen',False)) or '__compiled__' in globals()

FROZEN=_is_frozen()

def _frozen_runtime_dir():
    """Directory of the real .exe (not the ephemeral onefile temp dir).

    Nuitka onefile runs the app from a temp extraction folder, so __file__ and
    sys.executable point there. The real binary's folder is exposed via the
    NUITKA_ONEFILE_DIRECTORY env var (captured early in main.py as
    SYRALINE_EXE_DIR), with the onefile parent process as a fallback.
    """
    for key in ('SYRALINE_EXE_DIR','NUITKA_ONEFILE_DIRECTORY'):
        value=os.environ.get(key)
        if value:
            return Path(value)
    parent=os.environ.get('NUITKA_ONEFILE_PARENT')
    if parent:
        try:
            import psutil
            return Path(psutil.Process(int(parent)).exe()).resolve().parent
        except Exception:
            pass
    return Path(sys.executable).resolve().parent

# Bundled resources (styles, legacy) travel inside the build and stay relative
# to this module. Writable data (Input/Output/Logs) must live next to the .exe,
# not in the onefile temp-extraction directory.
if FROZEN:
    RUNTIME_DIR=_frozen_runtime_dir()
    PROJECT_DIR=RUNTIME_DIR
else:
    PROJECT_DIR=APP_DIR.parent
    RUNTIME_DIR=PROJECT_DIR
LEGACY_DIR=APP_DIR/'lib'/'legacy'
STYLES_DIR=APP_DIR/'styles'
INPUT_DIR=RUNTIME_DIR/'Input'
OUTPUT_DIR=RUNTIME_DIR/'Output'
DOCS_DIR=RUNTIME_DIR/'Docs'
SCREENSHOTS_DIR=OUTPUT_DIR/'Screenshots'

def resolve_input_path(value):
    """Relative user files belong to Input; explicit absolute paths stay valid."""
    path=Path(str(value).strip().strip('"').strip("'")).expanduser()
    if path.is_absolute():return resolve_relocated_input(path)
    if path.drive:raise ValueError('Chemin absolu requis pour un lecteur / Absolute drive path required')
    parts=path.parts
    if parts and parts[0].casefold() in {'input','syraline - input'}:parts=parts[1:]
    candidate=INPUT_DIR.joinpath(*parts).resolve()
    if not candidate.is_relative_to(INPUT_DIR.resolve()):
        raise ValueError('Chemin relatif hors Input : utiliser un chemin absolu / Use an absolute path outside Input')
    return candidate

def ensure_data_dirs():
    for directory in (INPUT_DIR,OUTPUT_DIR,SCREENSHOTS_DIR):directory.mkdir(parents=True,exist_ok=True)

def resolve_relocated_input(value):
    """Resolve old project-owned input paths without rewriting user settings."""
    path=Path(value).expanduser()
    if path.exists():return path
    if not path.is_absolute():return path
    for old,new in [(PROJECT_DIR/'VIP-Test',INPUT_DIR/'VIP-Test'),(PROJECT_DIR/'SyraLine - Input',INPUT_DIR),(PROJECT_DIR.parent/'SyraLine'/'Input',INPUT_DIR)]:
        try:relative=path.relative_to(old)
        except ValueError:continue
        candidate=new/relative
        if candidate.exists() and candidate.resolve().is_relative_to(INPUT_DIR.resolve()):return candidate
    return path
