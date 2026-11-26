"""SyraLine application launcher."""
import os as _os
# Capture the real onefile executable directory before Nuitka consumes the var,
# so Input/Output land next to the .exe (see lib/constants._frozen_runtime_dir).
_onefile_dir = _os.environ.get('NUITKA_ONEFILE_DIRECTORY')
if _onefile_dir:
    _os.environ['SYRALINE_EXE_DIR'] = _onefile_dir
from lib.entry import run_syraline
if __name__ == '__main__':
    try:
        run_syraline()
    except Exception:
        import sys
        import traceback
        from pathlib import Path
        from datetime import datetime
        report = traceback.format_exc()
        folder = Path(__file__).resolve().parent.parent / 'Output' / 'Logs'
        try:
            folder.mkdir(parents=True, exist_ok=True)
            log = folder / ('startup-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.log')
            log.write_text(report, encoding='utf-8')
            print('Startup error / Erreur au demarrage. Log: ' + str(log), file=sys.stderr)
        except OSError:
            pass
        # En build compilé, ne pas déverser la pile complète à l'écran (fuite de
        # logique interne) ; le fichier log ci-dessus reste pour le diagnostic.
        frozen = bool(getattr(sys, 'frozen', False)) or '__compiled__' in globals()
        if not frozen:
            print(report, file=sys.stderr)
        sys.exit(1)
