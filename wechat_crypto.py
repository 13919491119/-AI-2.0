"""WeChat 消息加解密基础实现 (安全模式骨架)

参考官方文档: https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Message_encryption_and_decryption.html

功能:
1. 校验/生成消息签名 (token, timestamp, nonce, msg_encrypt)
2. AES-CBC 解密 & 加密 (PKCS#7) 兼容微信格式
3. 仅在提供 WECHAT_ENCODING_AES_KEY & WECHAT_APPID 时启用

注意: 这是骨架实现，未做大规模性能优化与重放攻击防护。
"""
from __future__ import annotations
import base64
import hashlib
import os
import struct
import time
from dataclasses import dataclass
from typing import Optional

try:
    from Crypto.Cipher import AES  # pytype: disable=import-error
except ImportError:  # pragma: no cover
    AES = None  # type: ignore

BLOCK_SIZE = 32


def _pkcs7_pad(data: bytes) -> bytes:
    pad_len = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
    if pad_len == 0:
        pad_len = BLOCK_SIZE
    return data + bytes([pad_len]) * pad_len


def _pkcs7_unpad(data: bytes) -> bytes:
    if not data:
        raise ValueError("empty data")
    pad_len = data[-1]
    if pad_len < 1 or pad_len > BLOCK_SIZE:
        raise ValueError("invalid padding")
    if data[-pad_len:] != bytes([pad_len]) * pad_len:
        raise ValueError("bad padding tail")
    return data[:-pad_len]


def sha1_hex(*parts: str) -> str:
    s = ''.join(sorted(parts))
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


def sha1_join(parts: list[str]) -> str:
    parts_sorted = sorted(parts)
    return hashlib.sha1(''.join(parts_sorted).encode()).hexdigest()


@dataclass
class WeChatCrypto:
    token: str
    aes_key: str  # 43字符Base64(去掉=) 原始 key
    appid: str

    def __post_init__(self):
        if len(self.aes_key) != 43:
            raise ValueError("EncodingAESKey 长度必须为43")
        self._key = base64.b64decode(self.aes_key + '=')
        self._iv = self._key[:16]
        if AES is None:
            raise RuntimeError("未安装 pycryptodome, 请 pip install pycryptodome")

    # 生成消息签名
    def sign(self, timestamp: str, nonce: str, msg_encrypt: str) -> str:
        parts = [self.token, timestamp, nonce, msg_encrypt]
        parts.sort()
        return hashlib.sha1(''.join(parts).encode()).hexdigest()

    # 解密收到的 Encrypt 字段
    def decrypt(self, cipher_text_b64: str) -> str:
        cipher_data = base64.b64decode(cipher_text_b64)
        cipher = AES.new(self._key, AES.MODE_CBC, iv=self._iv)
        plain_padded = cipher.decrypt(cipher_data)
        plain = _pkcs7_unpad(plain_padded)
        # 16字节随机 + 4字节网络序内容长度 + xml + appid
        if len(plain) < 20:
            raise ValueError("解密内容过短")
        content_len = struct.unpack('!I', plain[16:20])[0]
        xml_part = plain[20:20+content_len]
        appid = plain[20+content_len:].decode('utf-8')
        if not appid.endswith(self.appid):  # 兼容可能填充
            raise ValueError("AppID 不匹配")
        return xml_part.decode('utf-8')

    # 加密回复 XML
    def encrypt(self, reply_xml: str) -> tuple[str, str, str, str]:
        import secrets
        rand16 = secrets.token_bytes(16)
        xml_bytes = reply_xml.encode('utf-8')
        msg_len = struct.pack('!I', len(xml_bytes))
        full = rand16 + msg_len + xml_bytes + self.appid.encode('utf-8')
        full_padded = _pkcs7_pad(full)
        cipher = AES.new(self._key, AES.MODE_CBC, iv=self._iv)
        encrypted = cipher.encrypt(full_padded)
        b64_enc = base64.b64encode(encrypted).decode('utf-8')
        timestamp = str(int(time.time()))
        nonce = secrets.token_hex(6)
        signature = self.sign(timestamp, nonce, b64_enc)
        return b64_enc, signature, timestamp, nonce


def build_crypto_from_env() -> Optional[WeChatCrypto]:
    token = os.environ.get('WECHAT_TOKEN')
    aes_key = os.environ.get('WECHAT_ENCODING_AES_KEY')
    appid = os.environ.get('WECHAT_APPID')
    if token and aes_key and appid:
        try:
            return WeChatCrypto(token=token.strip(), aes_key=aes_key.strip(), appid=appid.strip())
        except Exception as e:  # pragma: no cover
            print(f"[WeChatCrypto] 初始化失败: {e}")
            return None
    return None
