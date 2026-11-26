# SyraLine — Licence & activation

SyraLine exige une **clé de licence valide** à chaque lancement (avant l'UI).
Deux backends sont fournis ; on choisit avec `BACKEND` dans
`SyraLine/lib/license_config.py` :

| Backend    | Clés gérées sur…                          | À utiliser si…                                  |
|------------|-------------------------------------------|-------------------------------------------------|
| `keyauth`  | ton tableau de bord **KeyAuth** (keyauth.cc) | tu veux un service hébergé, prêt à l'emploi (**défaut**) |
| `server`   | le serveur **FastAPI** fourni (`server/`) | tu veux héberger toi-même (voir `server/README.md`) |

L'écran d'activation, la liaison machine (HWID) et la tolérance hors-ligne
(`OFFLINE_GRACE_DAYS`, 7 jours) sont communs aux deux.

---

## Backend KeyAuth (défaut)

### 1. Crée ton application KeyAuth
Sur https://keyauth.cc : connecte-toi → **Create Application**. Note, depuis
l'onglet de l'app :
- **App name** (`name`)
- **OwnerID** (`ownerid`, 10 caractères)
- **Version** (en général `1.0`)

> Ta **Seller Key** reste privée et côté serveur uniquement — elle n'est **pas**
> utilisée par le client SyraLine. Ne la mets jamais dans l'app.

### 2. Renseigne le client
Édite `SyraLine/lib/license_config.py` :

```python
BACKEND = 'keyauth'
KEYAUTH_NAME    = 'nom-de-ton-app'
KEYAUTH_OWNERID = 'ton-owner-id'
KEYAUTH_VERSION = '1.0'
```

(ou via variables d'environnement : `SYRALINE_KEYAUTH_NAME`,
`SYRALINE_KEYAUTH_OWNERID`, `SYRALINE_KEYAUTH_VERSION`.)

### 3. Génère des clés
Dans le tableau de bord KeyAuth : onglet **Licenses → Generate**. Tu choisis la
durée, le niveau d'abonnement, le nombre de machines (HWID) par clé, etc.
Tu peux aussi **révoquer / ban / reset HWID** d'une clé depuis le dashboard.

### 4. C'est prêt
Au lancement, SyraLine demande une clé, appelle KeyAuth (`init` puis `license`),
lie la clé au **HWID** de la machine, puis se souvient de l'activation.
Les réponses KeyAuth sont vérifiées par **signature Ed25519** (anti-serveur
falsifié) — cela nécessite le paquet `cryptography` (déjà dans
`requirements.txt`).

- HWID utilisé : `MachineGuid` (Windows), `/etc/machine-id` (Linux),
  `IOPlatformUUID` (macOS). Il s'affiche sur l'écran d'activation (utile pour un
  reset HWID côté dashboard).
- Si tu ne peux pas installer `cryptography`, mets
  `KEYAUTH_REQUIRE_SIGNATURE = False` (confiance TLS seule).

---

## Backend serveur auto-hébergé

Mets `BACKEND = 'server'` et suis `server/README.md` (lancer l'API, générer les
clés avec `admin.py`, pointer `LICENSE_API_BASE` + `LICENSE_SECRET`).

---

## Développement

Pour sauter la vérification pendant le dev :

```powershell
$env:SYRALINE_LICENSE_SKIP = "1"
```

## Portée de la protection

C'est une **dissuasion**, pas un DRM infaillible : le client est en Python, donc
quelqu'un avec le code source peut contourner le contrôle. L'intérêt réel :
centraliser les clés, lier au HWID, révoquer à distance, et bloquer le partage
de clés occasionnel. Pour durcir, tu peux compiler/obfusquer le client
(PyInstaller + un obfuscateur) — dis-le-moi si tu veux cette étape.
