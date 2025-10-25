import requests
import os

def send_wechat_alert(msg, sckey=None):
    """
    企业微信/Server酱推送（示例：Server酱）
    sckey: Server酱的SCKEY，或企业微信API
    """
    if sckey is None:
        sckey = os.environ.get('WECHAT_SCKEY')
    if not sckey:
        print('[微信告警] 未配置SCKEY，无法推送')
        return False
    url = f'https://sctapi.ftqq.com/{sckey}.send'
    data = {'title': 'AI系统告警', 'desp': msg}
    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code == 200:
            print('[微信告警] 推送成功')
            return True
        else:
            print(f'[微信告警] 推送失败: {resp.text}')
            return False
    except Exception as e:
        print(f'[微信告警] 推送异常: {e}')
        return False
