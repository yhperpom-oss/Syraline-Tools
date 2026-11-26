"""Offline admin CLI for the SyraLine license database.

Talks to the SQLite database directly (no running server required).

    python admin.py create --count 5 --max 1 --days 365 --note "batch march"
    python admin.py list
    python admin.py revoke ABCDE-FGHJK-LMNPQ-RSTUV
    python admin.py restore ABCDE-FGHJK-LMNPQ-RSTUV
"""
import argparse
import time

import db
import keygen


def _iso(ts):
    if not ts:
        return 'never'
    return time.strftime('%Y-%m-%d', time.gmtime(ts))


def cmd_create(args):
    db.init_db()
    expires_at = time.time() + args.days * 86400 if args.days > 0 else 0.0
    for _ in range(args.count):
        key = keygen.new_key()
        db.add_key(key, max_activations=args.max, expires_at=expires_at, note=args.note)
        print(key)


def cmd_list(args):
    db.init_db()
    rows = db.list_keys()
    if not rows:
        print('(no keys)')
        return
    print(f'{"KEY":25} {"STATUS":8} {"USES":>5} {"MAX":>4}  {"EXPIRES":10}  NOTE')
    for r in rows:
        print(f'{r["key"]:25} {r["status"]:8} {r["activations"]:>5} '
              f'{r["max_activations"]:>4}  {_iso(r["expires_at"]):10}  {r["note"]}')


def cmd_revoke(args):
    db.init_db()
    print('revoked' if db.set_status(args.key, 'revoked') else 'key not found')


def cmd_restore(args):
    db.init_db()
    print('restored' if db.set_status(args.key, 'active') else 'key not found')


def main():
    parser = argparse.ArgumentParser(description='SyraLine license admin')
    sub = parser.add_subparsers(dest='command', required=True)

    c = sub.add_parser('create', help='generate keys')
    c.add_argument('--count', type=int, default=1)
    c.add_argument('--max', type=int, default=1, help='max machines per key')
    c.add_argument('--days', type=int, default=0, help='validity in days (0 = never)')
    c.add_argument('--note', default='')
    c.set_defaults(func=cmd_create)

    sub.add_parser('list', help='list keys').set_defaults(func=cmd_list)

    r = sub.add_parser('revoke', help='revoke a key')
    r.add_argument('key')
    r.set_defaults(func=cmd_revoke)

    s = sub.add_parser('restore', help='re-activate a revoked key')
    s.add_argument('key')
    s.set_defaults(func=cmd_restore)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
