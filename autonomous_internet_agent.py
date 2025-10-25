"""
autonomous_internet_agent.py
系统自主联网代理：在无需人工干预的情况下，按需进行联网搜索/抓取/摘要。

功能特性：
- 复用 internet_research.research_and_summarize
- 简易本地缓存（JSON 文件），支持 TTL
- 全局开关（INTERNET_AGENT_ENABLED）与速率限制（INTERNET_AGENT_RATE_LIMIT）
- 统一写入报告到 reports/ 目录，便于后续分析/归档
"""
from __future__ import annotations

import os
import json
import time
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional

from internet_research import research_and_summarize, simple_summarize


def _ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def _slugify(text: str, max_len: int = 60) -> str:
    s = "".join(ch if ch.isalnum() else "-" for ch in text)
    while "--" in s:
        s = s.replace("--", "-")
    s = s.strip("-")
    if len(s) > max_len:
        s = s[:max_len].rstrip("-")
    return s or "query"


class InternetAgent:
    def __init__(
        self,
        enabled: Optional[bool] = None,
        rate_limit_seconds: Optional[int] = None,
        cache_path: str = ".internet_cache.json",
        last_call_path: str = ".internet_last_call.txt",
        reports_dir: str = "reports",
    ) -> None:
        self.enabled = enabled if enabled is not None else (os.getenv("INTERNET_AGENT_ENABLED", "1") != "0")
        self.rate_limit_seconds = (
            rate_limit_seconds if rate_limit_seconds is not None else int(os.getenv("INTERNET_AGENT_RATE_LIMIT", "60"))
        )
        self.cache_path = cache_path
        self.last_call_path = last_call_path
        self.reports_dir = reports_dir
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()
        _ensure_dir(self.reports_dir)

    # --------------- 缓存管理 ---------------
    def _load_cache(self) -> None:
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
        except Exception:
            self._cache = {}

    def _save_cache(self) -> None:
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _cache_key(self, query: str) -> str:
        h = hashlib.sha256(query.strip().encode("utf-8")).hexdigest()
        return h

    def _get_last_call_ts(self) -> float:
        try:
            if os.path.exists(self.last_call_path):
                with open(self.last_call_path, "r", encoding="utf-8") as f:
                    return float(f.read().strip() or 0)
        except Exception:
            pass
        return 0.0

    def _set_last_call_ts(self, ts: float) -> None:
        try:
            with open(self.last_call_path, "w", encoding="utf-8") as f:
                f.write(str(ts))
        except Exception:
            pass

    # --------------- 对外核心API ---------------
    def research(
        self,
        query: str,
        max_results: int = 3,
        freshness_ttl: int = 6 * 3600,  # 6小时
        wait_for_rate_limit: bool = True,
    ) -> Dict[str, Any]:
        """
        进行联网研究：若缓存存在且在TTL内，优先返回缓存；否则访问网络。
        """
        if not self.enabled:
            return {
                "summary": simple_summarize(query),
                "sources": [],
                "cached": False,
                "enabled": False,
            }

        key = self._cache_key(query)
        now = time.time()
        cached = self._cache.get(key)
        if cached and (now - cached.get("ts", 0)) < freshness_ttl:
            return {**cached.get("data", {}), "cached": True, "enabled": True}

        # 速率限制
        last_ts = self._get_last_call_ts()
        delta = now - last_ts
        if delta < self.rate_limit_seconds:
            if wait_for_rate_limit:
                time.sleep(self.rate_limit_seconds - delta)
            else:
                # 返回简易摘要，避免频繁外网请求
                return {
                    "summary": simple_summarize(query),
                    "sources": [],
                    "cached": False,
                    "enabled": True,
                    "rate_limited": True,
                }

        try:
            result = research_and_summarize(query, max_results=max_results)
            # 若未配置搜索API且无来源，自动回退到默认URL抓取，确保具备联网能力
            summary_text = (result.get("summary") or "")
            sources_list = result.get("sources") or []
            if (not sources_list) and ("未配置搜索API" in summary_text) and (not query.strip().lower().startswith("url:")):
                fallback_urls_env = os.getenv(
                    "INTERNET_AGENT_FALLBACK_URLS",
                    "https://www.wikipedia.org,https://news.ycombinator.com,https://www.python.org",
                )
                fallback_urls = [u.strip() for u in fallback_urls_env.split(",") if u.strip()]
                combined_sources = []
                combined_summary_parts = [summary_text.strip()]
                for u in fallback_urls[:2]:  # 最多抓取前两个，避免过多请求
                    try:
                        fr = research_and_summarize(f"url: {u}", max_results=1)
                        if fr.get("summary"):
                            combined_summary_parts.append(fr["summary"].strip())
                        if fr.get("sources"):
                            combined_sources.extend(fr["sources"])
                    except Exception:
                        pass
                if combined_sources:
                    result = {
                        "summary": "\n\n".join([p for p in combined_summary_parts if p]),
                        "sources": combined_sources,
                    }
            self._cache[key] = {"ts": time.time(), "data": result}
            self._save_cache()
            self._set_last_call_ts(time.time())
            # 写报告
            self._write_report(query, result)
            result.update({"cached": False, "enabled": True})
            return result
        except Exception as e:
            # 失败时，返回降级摘要
            fallback = {
                "summary": f"[联网失败，返回本地降级摘要] {simple_summarize(query)}\n原因: {e}",
                "sources": [],
                "cached": False,
                "enabled": True,
                "error": str(e),
            }
            return fallback

    # --------------- 报告输出 ---------------
    def _write_report(self, query: str, result: Dict[str, Any]) -> Optional[str]:
        try:
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            slug = _slugify(query)
            md_path = os.path.join(self.reports_dir, f"internet_{ts}_{slug}.md")
            lines = [
                f"# 联网研究报告: {query}",
                f"- 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- 缓存命中: 否",
                "",
                "## 摘要",
                result.get("summary", "(无)"),
                "",
                "## 来源",
            ]
            sources = result.get("sources") or []
            for i, src in enumerate(sources, 1):
                lines.append(f"{i}. {src}")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return md_path
        except Exception:
            return None
