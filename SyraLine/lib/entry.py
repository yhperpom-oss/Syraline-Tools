"""Application entry point shared by all launch methods."""
import argparse
from .deps import bootstrap
from .localization import LANGUAGES

def run_syraline(argv=None):
    parser = argparse.ArgumentParser(description='SyraLine')
    parser.add_argument('--no-boot', action='store_true')
    parser.add_argument('--tool', help='Tool identifier; see --list-tools')
    parser.add_argument('--lang', choices=tuple(LANGUAGES))
    parser.add_argument('--list-tools', action='store_true')
    args = parser.parse_args(argv)
    bootstrap()
    # Garde anti-debug (uniquement en build compilé ; no-op en dev).
    from .antidebug import guard
    guard()
    from .update_check import require_current_version
    if not require_current_version(args.lang):
        return
    from .constants import ensure_data_dirs
    ensure_data_dirs()
    # Outils VIP : chargés UNIQUEMENT depuis le pack chiffré, et seulement si une
    # licence KeyAuth valide permet au serveur de libérer la clé de déchiffrement.
    # Sans licence valide, ce code n'existe pas dans le build open source.
    try:
        from .vip_premium import load_premium_tools
        _premium = load_premium_tools()
        if _premium:
            from tools import core as _core
            _seen = {(t.category, t.name) for t in _core.TOOLS}
            _core.TOOLS.extend(t for t in _premium if (t.category, t.name) not in _seen)
    except Exception:
        pass
    from .pages import TOOL_IDS
    if args.list_tools:
        for key, (category, name) in TOOL_IDS.items():
            print(f'{key:24} {category} / {name}')
        return
    if args.tool and args.tool not in TOOL_IDS:
        parser.error('Unknown tool: ' + args.tool)
    from .ui import SyraLineApp
    app = SyraLineApp(boot=not args.no_boot and (not args.tool), initial_tool=TOOL_IDS.get(args.tool), language=args.lang, welcome_links=False)
    app.run()
    # Après une première activation VIP, l'app demande un rechargement pour charger
    # les outils VIP du pack chiffré (ils ne se chargent qu'au démarrage).
    if getattr(app, '_needs_reload', False):
        import os
        import sys
        # --no-boot : on saute l'intro au rechargement (l'utilisateur vient de la voir).
        reload_args = [a for a in sys.argv if a != '--no-boot'] + ['--no-boot']
        try:
            os.execv(sys.executable, [sys.executable, *reload_args])
        except Exception:
            pass
