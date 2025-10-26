"""
互联网检索与摘要模块
- 支持：
  1) 通过 SerpAPI 或 Bing Web Search API 进行网页检索（需在环境中配置密钥）
  2) 直接抓取指定 URL（前缀：url: 或 抓取:）
  3) 提取网页正文并生成摘要（优先 Deepseek API，总结失败时回退为本地简要摘要）

环境变量：
- SERPAPI_KEY: 使用 SerpAPI 时需要，参考 https://serpapi.com/
- BING_SEARCH_KEY: 使用 Bing Web Search 时需要
- BING_SEARCH_ENDPOINT: 形如 https://api.bing.microsoft.com/v7.0/search
- DEEPSEEK_API_KEY: 使用 Deepseek 生成摘要时需要

用法示例：
from internet_research import research_and_summarize
result = research_and_summarize("联网查询: 量子计算 最新进展", max_results=3)
print(result["summary"])  # 摘要
print(result["sources"])  # 引用链接
"""
from __future__ import annotations
from typing import List, Dict, Optional
import os, re, time

# 延迟导入，避免在未安装时阻塞模块加载
def _get_requests():
    try:
        import requests  # type: ignore
        return requests
    except Exception:
        return None

def _get_bs4():
    try:
        from bs4 import BeautifulSoup  # type: ignore
        return BeautifulSoup
    except Exception:
        return None

DEFAULT_TIMEOUT = float(os.getenv("WEB_TIMEOUT", "12"))
UA = os.getenv("WEB_UA", "Mozilla/5.0 (compatible; CelestialNexusBot/1.0; +https://example.com/bot)")

def _http_get(url: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    headers = {"User-Agent": UA}
    req = _get_requests()
    if req is None:
        raise RuntimeError("requests 未安装，无法进行联网抓取。请安装 requests 或使用 'url:' 直接抓取前先安装依赖。")
    resp = req.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    # 只取文本内容
    return resp.text

def extract_text(html: str, max_chars: int = 12000) -> str:
    BS = _get_bs4()
    if BS is not None:
        soup = BS(html, "html.parser")
        # 去除脚本与样式
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(" ")
    else:
        # 简易回退：移除标签，压缩空白
        text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]

def serpapi_search(query: str, num: int = 3) -> List[str]:
    req = _get_requests()
    if req is None:
        return []
    key = os.getenv("SERPAPI_KEY")
    if not key:
        return []
    # SerpAPI Google Search
    url = "https://serpapi.com/search.json"
    params = {"q": query, "engine": "google", "num": max(1, min(num, 10)), "api_key": key}
    r = req.get(url, params=params, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    links: List[str] = []
    for it in (data.get("organic_results") or [])[:num]:
        link = it.get("link")
        if link:
            links.append(link)
    return links

def bing_search(query: str, num: int = 3) -> List[str]:
    req = _get_requests()
    if req is None:
        return []
    key = os.getenv("BING_SEARCH_KEY")
    endpoint = os.getenv("BING_SEARCH_ENDPOINT")
    if not key or not endpoint:
        return []
    headers = {"Ocp-Apim-Subscription-Key": key}
    params = {"q": query, "count": max(1, min(num, 10))}
    r = req.get(endpoint, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    j = r.json()
    links: List[str] = []
    for it in (j.get("webPages", {}).get("value", []))[:num]:
        url = it.get("url")
        if url:
            links.append(url)
    return links

def simple_summarize(text: str, query: Optional[str] = None, max_chars: int = 900) -> str:
    if not text:
        return "未获取到可摘要的文本内容。"
    head = text[:max_chars]
    if query:
        return f"【简要摘要 - 本地】\n主题: {query}\n内容节选: {head}..."
    return f"【简要摘要 - 本地】\n{head}..."

def deepseek_summarize(text: str, query: Optional[str] = None, max_tokens: int = 512) -> Optional[str]:
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        return None
    try:
        from deepseek_api import DeepseekAPI  # type: ignore
        api = DeepseekAPI(api_key=key)
        prompt = (
            f"请基于以下资料生成聚合摘要，列出3-5条要点，并给出1句结论。\n"
            f"任务: {query or '主题未提供'}\n"
            f"资料: {text[:4000]}"
        )
        resp = api.chat([
            {"role": "system", "content": "你是专业的信息检索与总结助手。"},
            {"role": "user", "content": prompt}
        ], temperature=0.3, max_tokens=max_tokens)
        content = resp.get("choices", [{}])[0].get("message", {}).get("content")
        return content or None
    except Exception:
        return None

def research_and_summarize(query: str, max_results: int = 3) -> Dict[str, object]:
    """
    智能检索与总结：
    - query 以 "url:" 或 "抓取:" 开头时，直接抓取该 URL
    - 否则：优先使用 SerpAPI/Bing 进行网页检索，抓取前若干条结果进行聚合
    返回：{"summary": str, "sources": [url,...]}
    """
    q = query.strip()
    sources: List[str] = []
    texts: List[str] = []

    # 直接URL抓取
    m = re.match(r"^(?:url:|抓取[:：])\s*(https?://\S+)", q, flags=re.I)
    if m:
        url = m.group(1)
        try:
            html = _http_get(url)
            txt = extract_text(html)
            sources.append(url)
            texts.append(txt)
        except Exception as e:
            return {"summary": f"抓取失败: {e}", "sources": []}
    else:
        # 查询语句清理
        q = re.sub(r"^(联网查询|搜索|research:|web:)[:：]?\s*", "", q, flags=re.I)
        links = serpapi_search(q, max_results)
        if not links:
            links = bing_search(q, max_results)
        if not links:
            # 无可用检索能力时降级提示
            return {"summary": "未配置/未安装网络检索依赖（SERPAPI/BING 或 requests），改用本地简要摘要。", "sources": []}
        for url in links[:max_results]:
            try:
                html = _http_get(url)
                txt = extract_text(html)
                sources.append(url)
                texts.append(txt)
                # 避免过多请求
                time.sleep(0.5)
            except Exception:
                continue

    combined = "\n\n".join(texts)[:12000]
    summary = deepseek_summarize(combined, query=q) or simple_summarize(combined or (q or ""), query=q)
    return {"summary": summary, "sources": sources}
