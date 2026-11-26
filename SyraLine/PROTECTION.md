# SyraLine — Compilation & protection anti-crack

Stratégie en 3 couches, de la plus importante à la moins importante :

1. **KeyAuth en ligne** (déjà en place) — la validation se fait côté serveur.
   C'est ta meilleure défense : sans le bon serveur, pas de « oui » valide
   (réponses signées Ed25519).
2. **Nuitka** — compile le Python en **vrai binaire natif C**. Plus de `.pyc`
   décompilable : c'est l'étape qui rend le reverse *beaucoup* plus pénible.
3. **Themida ou VMProtect** — protège le `.exe` natif (anti-debug, anti-dump,
   anti-tamper, virtualisation). C'est toi qui lances cette étape avec ta licence.

> ⚠️ Aucune de ces couches ne rend l'app « incrackable ». Tout ce qui tourne sur
> la machine du client peut, avec assez d'efforts, être contourné. Le but est de
> rendre le crack **long et coûteux** — assez pour décourager.

---

## Étape 1 — Compiler avec Nuitka

Depuis le dossier de l'app (celui avec `main.py`) :

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

- Idéalement avec **Python 3.12** (les wheels de `requirements.txt` sont figées
  pour cette version). Le script prend `py -3.12` s'il existe.
- Nuitka télécharge tout seul son compilateur C (MinGW64) au premier run.
- Résultat : **`build-out\SyraLine.exe`** (un seul fichier natif).
- Place `SyraLine.exe` à la racine (à côté des dossiers `Input/`, `Output/` qui
  se créeront automatiquement à côté de l'exe).

Teste l'exe nu **avant** de le protéger (l'écran d'activation KeyAuth doit
apparaître et une vraie clé doit l'ouvrir).

---

## Étape 2a — Protéger avec Themida (recommandé)

Themida est généralement considéré comme le plus agressif. Ouvre
`SyraLine.exe` dans Themida et active :

- **Protection Options**
  - Virtual Machine : `Mutate + Virtualize` (ou un niveau `CISC`/`Tiger`).
  - Anti-Debugger : **Ultra** (Detection + Advanced).
  - Anti-Dump : ✔
  - Anti-Patch / File Integrity : ✔ (bloque le patch binaire — essentiel ici).
  - Resource Encryption : ✔
  - Memory Guard : ✔
- **Advanced Options**
  - Anti-VMWare/Sandbox : selon ton public (peut gêner des users légitimes en VM).
  - Metamorph / Entry Point Obfuscation : ✔
- Garde **« Application has a console »** coché (c'est une app terminal).
- Compile → `SyraLine_protected.exe`, puis re-teste l'activation.

## Étape 2b — Protéger avec VMProtect (alternative)

Ouvre `SyraLine.exe` dans VMProtect :

- Onglet **Functions** : « Compilation Type » global = **Virtualization** (ou
  `Ultra` = Mutation+Virtualization) ; pour un exe Nuitka tu protèges l'ensemble
  (tu n'as pas de marqueurs SDK dans le source compilé).
- Onglet **Options** :
  - **Memory Protection** ✔ (anti-patch mémoire)
  - **Import Protection** ✔
  - **Resource Protection** ✔
  - **Pack the Output File** ✔
  - **Detection: Debugger (user+kernel mode)** ✔, **Virtualization Tools** selon public.
- « Project Options → Application type : Console ».
- Compile → re-teste.

---

## Étape 3 — Le vrai durcissement anti-crack (fortement conseillé)

Un gate booléen (`require_license() → True/False`) reste la cible n°1 : un
cracker cherche le saut conditionnel et le force. Pour rendre ça **inutile**,
fais en sorte que l'app **ne puisse pas fonctionner sans le serveur** :

- Dans KeyAuth, utilise les **App Variables / Files** : stocke côté serveur une
  donnée dont l'app a *réellement* besoin (une valeur de config, une clé de
  déchiffrement d'une ressource, etc.) et récupère-la seulement après un
  `license()` réussi. Si on patche le check, la donnée manque → l'app casse.
- Évite un unique `if ok: ...` loin de l'usage : utilise le token/HWID renvoyé
  dans la logique réelle. On peut l'implémenter ensemble si tu veux (ex.
  déchiffrer les modules/outils avec une clé fournie par KeyAuth).

Sans cette couche, Nuitka + Themida ralentissent le crack ; **avec** elle, le
crack devient quasiment une réécriture.

---

## Rappels

- Ne distribue **jamais** le `.py`/les sources : seulement l'exe protégé.
- Regénère ton **Application Secret** KeyAuth (tu l'as partagé en clair).
- Signe ton exe (certificat Authenticode) pour réduire les alertes SmartScreen.
