"""License-key generation (random, human-readable, unambiguous alphabet)."""
import secrets

# No 0/O/1/I to avoid transcription mistakes.
ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
GROUPS = 4
GROUP_LEN = 5


def new_key():
    groups = [''.join(secrets.choice(ALPHABET) for _ in range(GROUP_LEN))
              for _ in range(GROUPS)]
    return '-'.join(groups)
