"""SyraLine licensing configuration.

Pick a backend and fill in its settings. Every value can also be overridden at
runtime with an environment variable (handy for testing).

Backends:
  'keyauth' -> validate keys against your KeyAuth app (keyauth.cc dashboard).
  'server'  -> validate keys against the bundled custom server (see ../server).
"""
import os

# Which licensing backend to use: 'keyauth' or 'server'.
# Override: SYRALINE_LICENSE_BACKEND
BACKEND = os.environ.get('SYRALINE_LICENSE_BACKEND', 'keyauth').strip().lower()

# How long the app keeps running if a previously-validated machine cannot
# reach the backend (temporary outage). After this it must re-validate.
OFFLINE_GRACE_DAYS = int(os.environ.get('SYRALINE_OFFLINE_GRACE_DAYS', '7'))

# Per-request network timeout, seconds.
REQUEST_TIMEOUT = int(os.environ.get('SYRALINE_LICENSE_TIMEOUT', '10'))


# --------------------------------------------------------------------------- #
# KeyAuth backend  (https://keyauth.cc dashboard -> your app)
# --------------------------------------------------------------------------- #
# Copy these from your KeyAuth application's dashboard. Name and OwnerID are not
# secret (they ship in every KeyAuth client); keep your *seller key* server-side
# only -- it is NOT needed or used here.
KEYAUTH_NAME = os.environ.get('SYRALINE_KEYAUTH_NAME', "Killwhisper's Application")
KEYAUTH_OWNERID = os.environ.get('SYRALINE_KEYAUTH_OWNERID', '8ujUh6NM0q')
KEYAUTH_VERSION = os.environ.get('SYRALINE_KEYAUTH_VERSION', '1.0')
# Optional: sha256 of the running file, if you use KeyAuth's hash check. Usually ''.
KEYAUTH_APP_HASH = os.environ.get('SYRALINE_KEYAUTH_HASH', '')
# Fail activation if the KeyAuth Ed25519 response signature cannot be verified
# (recommended). Requires the `cryptography` package. Set to '0' to allow
# TLS-only trust when cryptography is missing.
KEYAUTH_REQUIRE_SIGNATURE = os.environ.get('SYRALINE_KEYAUTH_REQUIRE_SIG', '1') != '0'


# --------------------------------------------------------------------------- #
# Custom-server backend  (the FastAPI server under SyraLine/server)
# --------------------------------------------------------------------------- #
# Base URL of your own license server (no trailing slash). Override: SYRALINE_LICENSE_API
LICENSE_API_BASE = os.environ.get(
    'SYRALINE_LICENSE_API', 'https://api.syraline.app'
).rstrip('/')

# Shared HMAC secret. MUST be identical to the server's LICENSE_SECRET.
# Override: SYRALINE_LICENSE_SECRET
LICENSE_SECRET = os.environ.get(
    'SYRALINE_LICENSE_SECRET', 'change-me-shared-secret-please'
)

# Logical product identifier sent to the custom server. Override: SYRALINE_PRODUCT_ID
PRODUCT_ID = os.environ.get('SYRALINE_PRODUCT_ID', 'syraline')


# --------------------------------------------------------------------------- #
# Pack VIP chiffré (open source)  — serveur de libération de la clé du pack.
# --------------------------------------------------------------------------- #
# Option A (recommandée, SANS serveur) : la clé du pack est stockée dans un
# fichier KeyAuth (dashboard → Files), téléchargeable uniquement après une
# licence valide. Mets ici l'ID du fichier KeyAuth qui contient la clé du pack
# (hex). Vide = option A désactivée. Override: SYRALINE_KEYAUTH_PACK_FILEID
KEYAUTH_PACK_FILEID = os.environ.get('SYRALINE_KEYAUTH_PACK_FILEID', '')

# Option B (alternative, avec serveur) : URL d'un serveur qui, après vérification
# de la licence KeyAuth côté serveur, renvoie la clé du pack (server/vip_keyserver.py).
# Utilisé seulement si KEYAUTH_PACK_FILEID est vide. Override: SYRALINE_VIP_PACK_API
VIP_PACK_API = os.environ.get('SYRALINE_VIP_PACK_API', 'https://syralinevip.yhperpom.workers.dev')
