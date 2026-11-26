"""Chiffrement du pack VIP premium (AES-256-GCM).

Principe : les outils VIP ne sont PAS distribués en clair dans le dépôt open
source. Ils sont empaquetés (zip) puis chiffrés avec une clé de 32 octets qui
reste UNIQUEMENT sur ton serveur. Le client ne peut déchiffrer qu'après avoir
obtenu la clé auprès du serveur, lequel ne la donne qu'après validation de la
licence KeyAuth (côté serveur, avec le seller key qui ne quitte jamais le
serveur). Sans clé valide → pas de clé de déchiffrement → le code VIP n'existe
jamais sur la machine du client.

Format du blob (tout en binaire) :
    MAGIC(8) | VERSION(1) | nonce(12) | ciphertext+tag(...)

Dépendance : `cryptography` (déjà dans requirements.txt).
"""
import hashlib
import os

MAGIC = b'SYRAVIP1'
VERSION = 1
NONCE_LEN = 12
KEY_LEN = 32


def _aesgcm(key: bytes):
    if not isinstance(key, (bytes, bytearray)) or len(key) != KEY_LEN:
        raise ValueError('Clé de pack invalide (32 octets requis).')
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    return AESGCM(bytes(key))


def new_key() -> bytes:
    """Génère une clé de pack aléatoire (à conserver côté serveur)."""
    return os.urandom(KEY_LEN)


def key_from_text(text: str) -> bytes:
    """Dérive une clé de 32 octets depuis une chaîne (ex. secret serveur).
    Pratique pour transporter la clé en base de données / variable d'env."""
    return hashlib.sha256(text.encode('utf-8')).digest()


def encrypt(plaintext: bytes, key: bytes) -> bytes:
    """Chiffre `plaintext` (le zip des outils VIP) → blob transportable."""
    nonce = os.urandom(NONCE_LEN)
    ciphertext = _aesgcm(key).encrypt(nonce, plaintext, MAGIC)
    return MAGIC + bytes([VERSION]) + nonce + ciphertext


def decrypt(blob: bytes, key: bytes) -> bytes:
    """Déchiffre un blob produit par encrypt(). Lève en cas de clé fausse ou
    d'altération (GCM authentifie le contenu : impossible de bidouiller le pack)."""
    if not isinstance(blob, (bytes, bytearray)) or len(blob) < len(MAGIC) + 1 + NONCE_LEN + 16:
        raise ValueError('Pack VIP illisible.')
    if bytes(blob[:len(MAGIC)]) != MAGIC:
        raise ValueError('Signature de pack VIP invalide.')
    if blob[len(MAGIC)] != VERSION:
        raise ValueError('Version de pack VIP non supportée.')
    offset = len(MAGIC) + 1
    nonce = bytes(blob[offset:offset + NONCE_LEN])
    ciphertext = bytes(blob[offset + NONCE_LEN:])
    from cryptography.exceptions import InvalidTag
    try:
        return _aesgcm(key).decrypt(nonce, ciphertext, MAGIC)
    except InvalidTag as exc:
        raise ValueError('Clé de pack invalide ou pack altéré.') from exc
