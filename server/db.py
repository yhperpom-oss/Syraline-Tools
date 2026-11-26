"""SQLite storage for the SyraLine license server."""
import os
import sqlite3
import time
from contextlib import contextmanager

DB_PATH = os.environ.get('SYRALINE_DB', os.path.join(os.path.dirname(__file__), 'licenses.db'))

SCHEMA = '''
CREATE TABLE IF NOT EXISTS keys (
    key             TEXT PRIMARY KEY,
    status          TEXT NOT NULL DEFAULT 'active',   -- active | revoked
    max_activations INTEGER NOT NULL DEFAULT 1,
    expires_at      REAL NOT NULL DEFAULT 0,          -- unix seconds, 0 = never
    note            TEXT NOT NULL DEFAULT '',
    created_at      REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS activations (
    key        TEXT NOT NULL,
    machine_id TEXT NOT NULL,
    token      TEXT NOT NULL,
    created_at REAL NOT NULL,
    last_seen  REAL NOT NULL,
    PRIMARY KEY (key, machine_id)
);
'''


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with connect() as conn:
        conn.executescript(SCHEMA)


def add_key(key, max_activations=1, expires_at=0.0, note=''):
    with connect() as conn:
        conn.execute(
            'INSERT OR REPLACE INTO keys (key, status, max_activations, expires_at, note, created_at) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (key, 'active', int(max_activations), float(expires_at), note, time.time()),
        )


def get_key(key):
    with connect() as conn:
        row = conn.execute('SELECT * FROM keys WHERE key = ?', (key,)).fetchone()
        return dict(row) if row else None


def list_keys():
    with connect() as conn:
        rows = conn.execute('SELECT * FROM keys ORDER BY created_at DESC').fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d['activations'] = conn.execute(
                'SELECT COUNT(*) FROM activations WHERE key = ?', (r['key'],)).fetchone()[0]
            out.append(d)
        return out


def set_status(key, status):
    with connect() as conn:
        cur = conn.execute('UPDATE keys SET status = ? WHERE key = ?', (status, key))
        return cur.rowcount > 0


def count_activations(key):
    with connect() as conn:
        return conn.execute('SELECT COUNT(*) FROM activations WHERE key = ?', (key,)).fetchone()[0]


def get_activation(key, machine_id):
    with connect() as conn:
        row = conn.execute(
            'SELECT * FROM activations WHERE key = ? AND machine_id = ?',
            (key, machine_id)).fetchone()
        return dict(row) if row else None


def upsert_activation(key, machine_id, token):
    now = time.time()
    with connect() as conn:
        existing = conn.execute(
            'SELECT created_at FROM activations WHERE key = ? AND machine_id = ?',
            (key, machine_id)).fetchone()
        created = existing['created_at'] if existing else now
        conn.execute(
            'INSERT OR REPLACE INTO activations (key, machine_id, token, created_at, last_seen) '
            'VALUES (?, ?, ?, ?, ?)',
            (key, machine_id, token, created, now),
        )


def touch_activation(key, machine_id):
    with connect() as conn:
        conn.execute('UPDATE activations SET last_seen = ? WHERE key = ? AND machine_id = ?',
                     (time.time(), key, machine_id))
