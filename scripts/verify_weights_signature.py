#!/usr/bin/env python3
"""Verify HMAC signature for a weights snapshot.

Usage: python3 scripts/verify_weights_signature.py <snapshot.json>
Returns exit code 0 on success, non-zero on mismatch or error.
"""
import sys
import os
import json
import hmac
import hashlib

KEY_PATH = os.path.join('scripts', 'weights_signing_key.bin')

def get_key():
    key = os.environ.get('WEIGHTS_SIGN_KEY')
    if key:
        return key.encode('utf-8')
    if os.path.exists(KEY_PATH):
        with open(KEY_PATH, 'rb') as f:
            return f.read()
    return None

def verify(path):
    sig_path = path + '.sig'
    if not os.path.exists(sig_path):
        print('Signature file missing:', sig_path)
        return 2
    key = get_key()
    if not key:
        print('No signing key available to verify. Set WEIGHTS_SIGN_KEY or provide scripts/weights_signing_key.bin')
        return 3
    with open(path, 'rb') as f:
        data = f.read()
    with open(sig_path, 'r', encoding='utf-8') as f:
        sig = json.load(f)
    expected = sig.get('hmac')
    hm = hmac.new(key, data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(hm, expected):
        print('Signature mismatch!')
        return 4
    print('Signature OK (key_id:', sig.get('key_id') + ')')
    return 0

def main():
    if len(sys.argv) < 2:
        print('Usage: verify_weights_signature.py <snapshot.json>')
        return 2
    return verify(sys.argv[1])

if __name__ == '__main__':
    raise SystemExit(main())
