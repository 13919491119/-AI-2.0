#!/usr/bin/env python3
import os, time, json, pathlib, re

ROOT = "/workspaces/-AI-2.0"
STATIC = os.path.join(ROOT, "static")
OUT_JSON = os.path.join(STATIC, "public_urls.json")

def load_dotenv_into_environ(env_path: str):
    try:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
                    if not m:
                        continue
                    k, v = m.group(1), m.group(2)
                    if v.startswith("\"") and v.endswith("\""):
                        v = v[1:-1]
                    if k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass

def main():
    # Load .env for NGROK_AUTH_TOKEN/NGROK_REGION if not already set
    load_dotenv_into_environ(os.path.join(ROOT, ".env"))

    try:
        from pyngrok import ngrok, conf
    except Exception as e:
        print("[ngrok] pyngrok 未安装或导入失败：", e, flush=True)
        print("[ngrok] 请在 .venv 中安装 pyngrok 或改用其他公开方案 (FRP/Nginx)", flush=True)
        time.sleep(5)
        return

    token = os.environ.get("NGROK_AUTH_TOKEN", "")
    region = os.environ.get("NGROK_REGION", "")
    if token:
        conf.get_default().auth_token = token
    if region:
        conf.get_default().region = region

    targets = {
        "report_frontend_8080": 8080,
        "static_8088": 8088,
        "api_8000": 8000,
    }
    urls = {}
    for name, port in targets.items():
        try:
            t = ngrok.connect(addr=port, proto="http", bind_tls=True)
            # prefer https
            url = t.public_url
            try:
                tunnels = ngrok.get_tunnels()
                https = [tt.public_url for tt in tunnels if tt.public_url.startswith("https://") and f":{port}" in (tt.config.get('addr','') if hasattr(tt, 'config') else '')]
                if https:
                    url = https[0]
            except Exception:
                pass
            urls[name] = url
            print(f"[ngrok] {name} -> {url}", flush=True)
        except Exception as e:
            print(f"[ngrok] 创建 {name} (:{port}) 隧道失败: {e}", flush=True)

    # write JSON for frontend consumption
    try:
        pathlib.Path(STATIC).mkdir(parents=True, exist_ok=True)
        with open(OUT_JSON, "w", encoding="utf-8") as f:
            json.dump({"timestamp": time.strftime('%Y-%m-%d %H:%M:%S'), "urls": urls}, f, ensure_ascii=False, indent=2)
        print(f"[ngrok] 写入 {OUT_JSON}", flush=True)
    except Exception as e:
        print("[ngrok] 写入 public_urls.json 失败：", e, flush=True)

    # keep process alive so tunnels persist
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
