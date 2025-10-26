from pyngrok import ngrok, conf
import os, time
token = os.environ.get('NGROK_AUTH_TOKEN','')
if token:
  conf.get_default().auth_token = token
region = os.environ.get('NGROK_REGION','')
if region:
  conf.get_default().region = region
# 建立HTTP隧道并启用TLS，从而提供HTTPS(443)地址
tunnel = ngrok.connect(addr=os.environ.get('WECHAT_PORT','9090'), proto='http', bind_tls=True)
# 优先选择HTTPS隧道
url = tunnel.public_url
try:
  tunnels = ngrok.get_tunnels()
  https = [t.public_url for t in tunnels if t.public_url.startswith('https://')]
  if https:
    url = https[0]
except Exception:
  pass
with open('ngrok_url.txt','w') as f:
  f.write(url)
print(url, flush=True)
while True:
  time.sleep(60)
