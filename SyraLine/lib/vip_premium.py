"""Chargement des outils VIP depuis le pack chiffré (open source compatible).

Les outils VIP ne sont PAS dans le dépôt : seul `vip_premium.enc` (chiffré) y est.
Au lancement, si une licence KeyAuth valide est mémorisée, le client demande la
clé du pack au serveur (qui ne la donne qu'après vérification de la licence),
déchiffre le pack en mémoire, et enregistre les outils VIP.

Sans licence valide → le serveur refuse la clé → le pack reste illisible →
les catégories VIP restent de simples cadenas sans code derrière.
"""
import io
import zipfile

from .constants import RUNTIME_DIR, APP_DIR

# Le pack chiffré peut être placé à côté de l'exe (RUNTIME_DIR) ou dans l'app.
_PACK_CANDIDATES = (RUNTIME_DIR / 'vip_premium.enc', APP_DIR / 'vip_premium.enc')


def _pack_path():
    for candidate in _PACK_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def _coerce_key(raw):
    """Normalise une donnée (octets bruts ou texte hex) en clé de 32 octets."""
    from . import vip_crypto
    if isinstance(raw, str):
        raw = raw.encode()
    if len(raw) == vip_crypto.KEY_LEN:
        return bytes(raw)
    try:
        key = bytes.fromhex(raw.decode('ascii').strip())
        return key if len(key) == vip_crypto.KEY_LEN else None
    except (ValueError, UnicodeDecodeError):
        return None


def _fetch_key_keyauth(license_key):
    """Option A (sans serveur) : récupère la clé depuis un fichier KeyAuth,
    accessible seulement après une licence valide (session authentifiée)."""
    from . import license_config as cfg, keyauth_client as ka
    fileid = getattr(cfg, 'KEYAUTH_PACK_FILEID', '').strip()
    if not fileid:
        return None
    try:
        app = ka.KeyAuthApp(cfg.KEYAUTH_NAME, cfg.KEYAUTH_OWNERID, cfg.KEYAUTH_VERSION,
                            cfg.KEYAUTH_APP_HASH, cfg.REQUEST_TIMEOUT, cfg.KEYAUTH_REQUIRE_SIGNATURE)
        if not app.license(license_key).get('success'):
            return None
        result = app.file(fileid)
    except Exception:
        return None
    if not result.get('success') or not result.get('data'):
        return None
    return _coerce_key(result['data'])


def _fetch_key_server(license_key):
    """Option B (serveur) : demande la clé au serveur de libération, qui vérifie
    la licence KeyAuth (clé + HWID) avant de la renvoyer."""
    from . import license_config as cfg
    url = getattr(cfg, 'VIP_PACK_API', '').strip()
    if not url:
        return None
    try:
        from . import keyauth_client as ka
        hwid = ka.get_hwid()
    except Exception:
        hwid = ''
    try:
        import requests
        # User-Agent de navigateur : évite les blocages anti-bot de Cloudflare.
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'}
        data = requests.post(url, json={'key': license_key, 'hwid': hwid},
                             headers=headers, timeout=cfg.REQUEST_TIMEOUT).json()
    except Exception:
        return None
    if not data.get('ok') or not data.get('pack_key'):
        return None
    return _coerce_key(data['pack_key'])


def _fetch_pack_key(license_key):
    """Clé du pack via KeyAuth (sans serveur) en priorité, sinon via un serveur."""
    return _fetch_key_keyauth(license_key) or _fetch_key_server(license_key)


def load_premium_tools():
    """Charge et renvoie la liste des outils VIP (objets Tool), ou [] si la
    licence/clé/pack n'est pas disponible. N'exécute rien sans clé valide."""
    pack = _pack_path()
    if pack is None:
        return []
    try:
        from .license_state import load_state, within_grace, key_expired, same_machine
        state = load_state()
        license_key = state.get('key', '')
        if not license_key or key_expired(state) or not within_grace(state) or not same_machine(state):
            return []
    except Exception:
        return []

    key = _fetch_pack_key(license_key)
    if not key:
        return []
    try:
        from . import vip_crypto
        plaintext = vip_crypto.decrypt(pack.read_bytes(), key)
    except Exception:
        return []

    tools = []

    def add(cat, name, fr, en, hint, fn, network=False):
        from tools.core import Tool
        tools.append(Tool(cat, name, fr, en, hint, fn, network))

    try:
        with zipfile.ZipFile(io.BytesIO(plaintext)) as archive:
            source = archive.read('premium_tools.py').decode('utf-8')
        namespace = {'__name__': 'syraline_premium'}
        exec(compile(source, 'vip_premium_pack', 'exec'), namespace)  # code à TOI, livré chiffré
        register = namespace.get('register')
        if callable(register):
            register(add)
    except Exception:
        return []
    return tools
