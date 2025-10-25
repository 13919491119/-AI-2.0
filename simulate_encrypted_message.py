#!/usr/bin/env python3
"""本地模拟发送一条加密微信消息到 /wechat

特性:
1. 自动加载当前目录 `.env.wechat` （若存在）
2. 支持命令行参数：
   - 第一个位置参数: 文本内容 (默认: '测试加密消息')
   - `--url <endpoint>` 指定目标（默认 http://127.0.0.1:9090/wechat）
3. 发送加密 POST，打印结果与解密关键字段提示

用法示例:
  python simulate_encrypted_message.py '加密测试' --url http://localhost:9090/wechat
"""
from __future__ import annotations
import os, time, sys, requests, argparse
from wechat_crypto import WeChatCrypto

def load_env_file(path: str = '.env.wechat') -> bool:
    if not os.path.exists(path):
        return False
    loaded = False
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            k = k.strip(); v = v.strip()
            if k and v and k not in os.environ:
                os.environ[k] = v
                loaded = True
    return loaded

def parse_args():
    p = argparse.ArgumentParser(description='WeChat AES 加密消息模拟发送器')
    p.add_argument('text', nargs='?', default='测试加密消息', help='要发送的文本内容')
    p.add_argument('--url', default=os.environ.get('WECHAT_URL','http://127.0.0.1:9090/wechat'), help='目标 /wechat 接口地址')
    return p.parse_args()

def main():
    # 自动加载 .env.wechat
    if load_env_file():
        print('[ENV] 已加载 .env.wechat')
    args = parse_args()
    text = args.text
    token = os.environ.get('WECHAT_TOKEN','celestial_nexus_ai_token')
    aes = os.environ.get('WECHAT_ENCODING_AES_KEY')
    appid = os.environ.get('WECHAT_APPID')
    if not (aes and appid):
        print('[ERR] 未发现加密环境变量 WECHAT_ENCODING_AES_KEY / WECHAT_APPID，无法模拟加密 (可先运行 enable_encrypted_mode.sh)')
        sys.exit(2)
    if len(aes) != 43:
        print('[ERR] WECHAT_ENCODING_AES_KEY 长度非43，当前长度:', len(aes))
        sys.exit(3)
    crypto = WeChatCrypto(token, aes, appid)
    xml_plain = f"""<xml><ToUserName><![CDATA[{appid}]]></ToUserName><FromUserName><![CDATA[user_openid]]></FromUserName><CreateTime>{int(time.time())}</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[{text}]]></Content><MsgId>1234567890</MsgId></xml>"""
    enc, sig, ts, nonce = crypto.encrypt(xml_plain)
    wrap = f"""<xml><Encrypt><![CDATA[{enc}]]></Encrypt><MsgSignature><![CDATA[{sig}]]></MsgSignature><TimeStamp>{ts}</TimeStamp><Nonce><![CDATA[{nonce}]]></Nonce></xml>"""
    url = args.url.rstrip('/') + f"?timestamp={ts}&nonce={nonce}&msg_signature={sig}&encrypt_type=aes"
    print('[SEND] POST', url)
    r = requests.post(url, data=wrap.encode('utf-8'), timeout=10, headers={'Content-Type':'application/xml'})
    print('[RESP] 状态:', r.status_code)
    txt = r.text
    if r.status_code == 200:
        if '<Encrypt>' in txt:
            print('[INFO] 收到加密响应(服务端已加密回包)，前200字:')
        else:
            print('[INFO] 收到明文或非预期响应，前200字:')
    else:
        print('[WARN] 非200响应，前200字:')
    print(txt[:200])

if __name__ == '__main__':
    main()
