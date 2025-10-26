#!/usr/bin/env python3
"""
简易互联网自检：
- 直接抓取 URL: https://www.python.org/
- 搜索查询（若有 SERPAPI/Bing 配置则走搜索，否则走降级提示）
输出：
- reports/internet_self_test_YYYYMMDD_HHMMSS.txt（人读）
- static/internet_self_test.json（机器读）
"""
import os, json, datetime, sys, importlib
from pathlib import Path

ROOT = "/workspaces/-AI-2.0"
REPORTS = os.path.join(ROOT, "reports")
STATIC = os.path.join(ROOT, "static")
os.makedirs(REPORTS, exist_ok=True)
os.makedirs(STATIC, exist_ok=True)
# 确保可以导入项目根目录下的模块
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# 尝试加载 .env（若安装了 python-dotenv），否则使用简易解析器
def _load_env_file(env_path: str):
    try:
        _dotenv = importlib.import_module("dotenv")
        if hasattr(_dotenv, "load_dotenv"):
            _dotenv.load_dotenv(dotenv_path=env_path)
            return
    except Exception:
        pass
    # 简易解析：仅支持 KEY=VALUE，忽略以#开头的注释
    try:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and v and k not in os.environ:
                            os.environ[k] = v
    except Exception:
        pass

_load_env_file(os.path.join(ROOT, ".env"))

def run_test():
    from internet_research import research_and_summarize, deepseek_summarize
    results = {
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "url_test": {},
        "search_test": {},
        "deepseek": {"enabled": bool(os.getenv("DEEPSEEK_API_KEY"))}
    }
    # URL 直连测试
    try:
        r = research_and_summarize("url:https://www.python.org/")
        results["url_test"] = {
            "ok": True,
            "summary_len": len(r.get("summary") or ""),
            "sources": r.get("sources") or []
        }
    except Exception as e:
        results["url_test"] = {"ok": False, "error": str(e)}
    # 搜索测试（若未配置 API Key 会返回降级提示）
    try:
        r = research_and_summarize("联网查询: OpenAI 最新动态", max_results=2)
        results["search_test"] = {
            "ok": True,
            "summary_len": len(r.get("summary") or ""),
            "sources": r.get("sources") or []
        }
    except Exception as e:
        results["search_test"] = {"ok": False, "error": str(e)}
    # Deepseek 连通性快速自检（优先通过封装方法，若失败再直接请求以获得错误细节）
    try:
        ds = deepseek_summarize("自检: 这是一段很短的文本", query="自检")
        results["deepseek"].update({
            "ok": bool(ds),
            "test_summary_len": len(ds or "")
        })
        if not ds and results["deepseek"].get("enabled"):
            try:
                from deepseek_api import DeepseekAPI  # type: ignore
                api = DeepseekAPI()
                ping = api.chat([
                    {"role": "system", "content": "你是健康检查助手。"},
                    {"role": "user", "content": "请仅回复: OK"}
                ], temperature=0.0, max_tokens=3)
                content = (ping.get("choices", [{}])[0].get("message", {}) or {}).get("content")
                ok = bool(content)
                results["deepseek"].update({
                    "ok": ok,
                    "direct_reply": content or ""
                })
            except Exception as e2:
                results["deepseek"].update({"ok": False, "error": str(e2)})
    except Exception as e:
        results["deepseek"].update({"ok": False, "error": str(e)})
    # 写文件
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    human = os.path.join(REPORTS, f"internet_self_test_{ts}.txt")
    with open(human, "w", encoding="utf-8") as f:
        f.write("互联网自检结果\n\n")
        f.write(json.dumps(results, ensure_ascii=False, indent=2))
        f.write("\n")
    machine = os.path.join(STATIC, "internet_self_test.json")
    with open(machine, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results, human, machine

if __name__ == "__main__":
    res, human, machine = run_test()
    print("自检完成：")
    print("- 文本：", human)
    print("- JSON：", machine)
