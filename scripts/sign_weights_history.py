#!/usr/bin/env python3
"""Sign a weights snapshot using HMAC-SHA256.

Usage: python3 scripts/sign_weights_history.py <snapshot.json>

Behavior:
- If environment variable WEIGHTS_SIGN_KEY is set, uses it as the HMAC key.
- Otherwise generates a local key at scripts/weights_signing_key.bin (0600) and reuses it.
- Writes a signature file alongside the snapshot with extension .sig containing JSON:
  {signed_at: <ts>, hmac: <hex>, key_id: <sha1-of-key>}
"""
import sys
import os
import hmac
import hashlib
import json
from datetime import datetime

KEY_PATH = os.path.join('scripts', 'weights_signing_key.bin')

def get_key():
    key = os.environ.get('WEIGHTS_SIGN_KEY')
    if key:
        return key.encode('utf-8')
    # ensure scripts dir exists
    os.makedirs('scripts', exist_ok=True)
    if os.path.exists(KEY_PATH):
        with open(KEY_PATH, 'rb') as f:
            return f.read()
    # generate a random key
    k = os.urandom(32)
    try:
        with open(KEY_PATH, 'wb') as f:
            f.write(k)
        os.chmod(KEY_PATH, 0o600)
    except Exception:
        pass
    return k

def sign_file(path):
    key = get_key()
    with open(path, 'rb') as f:
        data = f.read()
    hm = hmac.new(key, data, hashlib.sha256).hexdigest()
    key_id = hashlib.sha1(key).hexdigest()[:12]
    sig = {'signed_at': datetime.utcnow().isoformat() + 'Z', 'hmac': hm, 'key_id': key_id}
    sig_path = path + '.sig'
    with open(sig_path, 'w', encoding='utf-8') as f:
        json.dump(sig, f, ensure_ascii=False, indent=2)
    print('Wrote signature to', sig_path)
    return sig_path

def main():
    if len(sys.argv) < 2:
        print('Usage: sign_weights_history.py <snapshot.json>')
        return 2
    path = sys.argv[1]
    if not os.path.exists(path):
        print('Snapshot not found:', path)
        return 3
    try:
        sign_file(path)
        return 0
    except Exception as e:
        print('Error signing file:', e)
        return 4

if __name__ == '__main__':
    raise SystemExit(main())
#!/usr/bin/env python3
"""
签名脚本：对 `reports/weights_history/*.json` 中缺少 `sha256` 字段的文件计算 SHA256 并写回。
"""
import os
import json
import hashlib

DIR = 'reports/weights_history'

if not os.path.isdir(DIR):
    print('weights_history 目录不存在，跳过')
    raise SystemExit(0)

for fn in os.listdir(DIR):
    if not fn.endswith('.json'):
        continue
    path = os.path.join(DIR, fn)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        print('无法读取', path)
        continue
    if 'sha256' in data:
        print('已签名，跳过', fn)
        continue
    content = json.dumps(data, ensure_ascii=False, indent=2)
    sha = hashlib.sha256(content.encode('utf-8')).hexdigest()
    data['sha256'] = sha
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print('已签名', fn)
    except Exception as e:
        print('写回失败', fn, e)
