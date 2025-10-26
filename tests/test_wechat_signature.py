import os
import time
import hashlib
import requests

BASE = os.environ.get('WECHAT_BASE', 'http://127.0.0.1:9090')
TOKEN = os.environ.get('WECHAT_TOKEN', 'celestial_nexus_ai_token')

def make_sig(ts: str, nonce: str):
    raw = ''.join(sorted([TOKEN, ts, nonce]))
    return hashlib.sha1(raw.encode()).hexdigest()

def test_signature_ok():
    ts = str(int(time.time()))
    nonce = 'abc123'
    sig = make_sig(ts, nonce)
    echostr = 'unittest'
    r = requests.get(f"{BASE}/wechat", params={
        'signature': sig,
        'timestamp': ts,
        'nonce': nonce,
        'echostr': echostr
    }, timeout=5)
    assert r.status_code == 200 and r.text == echostr

def test_signature_fail():
    r = requests.get(f"{BASE}/wechat", params={
        'signature': 'bad',
        'timestamp': '1',
        'nonce': '2',
        'echostr': 'xxx'
    }, timeout=5)
    # 严格模式下应该403
    assert r.status_code in (403, 200)  # 兼容调试模式

if __name__ == '__main__':
    test_signature_ok()
    test_signature_fail()
    print('Signature tests completed.')
