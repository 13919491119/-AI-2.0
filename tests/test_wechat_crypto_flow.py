import os, time, hashlib, xml.etree.ElementTree as ET
import pytest
from wechat_crypto import WeChatCrypto

@pytest.mark.skipif('WECHAT_ENCODING_AES_KEY' not in os.environ or 'WECHAT_APPID' not in os.environ, reason='encryption env not set')
def test_encrypt_decrypt_roundtrip():
    token = os.environ['WECHAT_TOKEN']
    aes_key = os.environ['WECHAT_ENCODING_AES_KEY']
    appid = os.environ['WECHAT_APPID']
    crypto = WeChatCrypto(token, aes_key, appid)
    sample = """<xml><ToUserName><![CDATA[toUser]]></ToUserName><FromUserName><![CDATA[fromUser]]></FromUserName><CreateTime>{}</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[测试加密链路]]></Content></xml>""".format(int(time.time()))
    enc, sig, ts, nonce = crypto.encrypt(sample)
    # 校验签名
    parts = [token, ts, nonce, enc]
    parts.sort()
    raw = ''.join(parts)
    assert hashlib.sha1(raw.encode()).hexdigest() == sig
    # 解密
    plain = crypto.decrypt(enc)
    assert '测试加密链路' in plain
