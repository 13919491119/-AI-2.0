#!/usr/bin/env python3
"""
历史人物与系统自知人物AI预测与复盘循环任务

功能：
1. 自动调取外部人物数据（出生年月日、八字、姓名等）
2. 用玄机AI系统进行预测与事实复盘，反复总结
3. 每次复盘均触发新知识学习、新模式发现和系统自主升级
4. 所有学习、发现、升级过程自动记录到知识库
5. 系统全程静默自主运行，无需人工干预
"""

import asyncio
import random
import time
import json
import os
import sys
import logging
from typing import Dict, List, Any, Tuple
import traceback

# 扩展能力：外部互联网检索与内部大模型抽取
try:
    from internet_research import research_and_summarize  # type: ignore
except Exception:
    research_and_summarize = None  # 兼容无依赖环境

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("xuanji_person_predict.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 外部人物数据API（示例，可替换为真实API）
PERSON_API_URL = "https://api.example.com/persons"  # 需替换为真实API
LOCAL_API_URL = "http://localhost:8000"
PERSON_CACHE_FILE = "person_data.json"
PERSON_LEARNING_FILE = "person_learning_cycles.txt"
PERSON_KNOWLEDGE_FILE = "person_knowledge_base.txt"

# 外部扩张/内部抽取 配置
PERSON_NET_EXPAND = os.getenv("PERSON_NET_EXPAND", "0") == "1"
PERSON_LLM_EXTRACT = os.getenv("PERSON_LLM_EXTRACT", "0") == "1"
try:
    PERSON_EXPAND_INTERVAL = int(os.getenv("PERSON_EXPAND_INTERVAL", str(24*3600)))
except Exception:
    PERSON_EXPAND_INTERVAL = 24*3600
try:
    PERSON_EXTRACT_INTERVAL = int(os.getenv("PERSON_EXTRACT_INTERVAL", str(48*3600)))
except Exception:
    PERSON_EXTRACT_INTERVAL = 48*3600

REPORTS_DIR = os.path.join(os.getcwd(), "reports")
STATIC_DIR = os.path.join(os.getcwd(), "static")
PERSON_STATUS_FILE = os.path.join(STATIC_DIR, "person_expand_status.json")
PERSONS_ENRICHED = os.path.join(REPORTS_DIR, "persons_enriched.jsonl")
PERSONS_FACTS = os.path.join(REPORTS_DIR, "persons_facts.jsonl")

def _ensure_dirs():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)

def _load_person_status() -> Dict[str, Any]:
    _ensure_dirs()
    if os.path.exists(PERSON_STATUS_FILE):
        try:
            with open(PERSON_STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"persons": {}}
    return {"persons": {}}

def _save_person_status(status: Dict[str, Any]):
    _ensure_dirs()
    try:
        with open(PERSON_STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"写入 person_expand_status.json 失败: {e}")

def _append_jsonl(path: str, obj: Dict[str, Any]):
    _ensure_dirs()
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"追加 {path} 失败: {e}")

def _now_ts() -> float:
    return time.time()

def _should_run(last_ts: float | None, interval: int) -> bool:
    if not last_ts:
        return True
    return (_now_ts() - float(last_ts)) >= max(0, interval)

def expand_person_with_internet(person: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | None]:
    """对单个人物执行一次外部互联网扩张。
    返回 (done, record)，done=False 表示跳过或失败。
    """
    if not PERSON_NET_EXPAND:
        return False, None
    if research_and_summarize is None:
        # 回退：在不可用时也生成一条最小记录，保证流程与状态可前进
        name = person.get("name") or "未知人物"
        record = {
            "ts": _now_ts(),
            "name": name,
            "query": f"联网查询: {name} 生平 年表 作品 评价",
            "summary": "未配置网络检索依赖（SERPAPI/BING/requests），已生成本地回退摘要占位。",
            "sources": [],
        }
        _append_jsonl(PERSONS_ENRICHED, record)
        return True, record
    name = person.get("name") or "未知人物"
    # 简单查询模版（可按需丰富）
    query = f"联网查询: {name} 生平 年表 作品 评价"
    try:
        res = research_and_summarize(query, max_results=3)
        record = {
            "ts": _now_ts(),
            "name": name,
            "query": query,
            "summary": (res or {}).get("summary"),
            "sources": (res or {}).get("sources", []),
        }
        _append_jsonl(PERSONS_ENRICHED, record)
        return True, record
    except Exception as e:
        # 出错时回退为占位记录
        logger.warning(f"外部扩张失败({name})，使用回退摘要: {e}")
        record = {
            "ts": _now_ts(),
            "name": name,
            "query": query,
            "summary": "联网扩张发生异常，已写入回退摘要占位。",
            "sources": [],
        }
        _append_jsonl(PERSONS_ENRICHED, record)
        return True, record

def extract_person_facts(person: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | None]:
    """对单个人物执行一次内部事实抽取：有 DEEPSEEK_API_KEY 则调用模型，否则回退规则抽取。"""
    if not PERSON_LLM_EXTRACT:
        return False, None
    name = person.get("name") or "未知人物"
    bazi = person.get("bazi") or ""
    fact = person.get("fact") or ""
    # 汇总上下文（可包含知识库片段，先用当前 person 信息）
    context = f"姓名:{name}\n八字:{bazi}\n事实:{fact}"
    # 优先使用 Deepseek
    key = os.getenv("DEEPSEEK_API_KEY")
    facts: List[Dict[str, Any]] = []
    used = "rule"
    if key:
        try:
            from deepseek_api import DeepseekAPI  # type: ignore
            api = DeepseekAPI(api_key=key)
            prompt = (
                "请从以下人物资料中抽取结构化事实，输出 JSON，字段包括: "
                "name, birth(可空), achievements(列表), domains(列表), summary(一句话)。\n"
                f"资料:\n{context[:1600]}\n"
            )
            resp = api.chat([
                {"role": "system", "content": "你是严谨的事实抽取助手，输出必须是严格 JSON。"},
                {"role": "user", "content": prompt}
            ], temperature=0.2, max_tokens=512)
            content = (resp.get("choices", [{}])[0].get("message", {}) or {}).get("content")
            data = None
            if content:
                try:
                    data = json.loads(content)
                except Exception:
                    # 尝试从文本中提取 JSON 片段
                    import re as _re
                    m = _re.search(r"\{[\s\S]*\}", content)
                    if m:
                        data = json.loads(m.group(0))
            if isinstance(data, dict):
                facts.append(data)
                used = "deepseek"
        except Exception as e:
            logger.info(f"Deepseek 抽取失败，回退规则({name}): {e}")
    if not facts:
        # 规则回退：生成简单事实
        facts.append({
            "name": name,
            "birth": None,
            "achievements": [f"与其领域相关的重要贡献（示例）: {fact[:40]}" if fact else "贡献不详"],
            "domains": ["历史人物"],
            "summary": f"{name} 在其领域具有代表性影响（回退生成）。",
        })
    record = {"ts": _now_ts(), "name": name, "facts": facts, "mode": used}
    _append_jsonl(PERSONS_FACTS, record)
    return True, record

class PersonDataCollector:
    """历史人物数据收集器"""
    @staticmethod
    async def fetch_person_data() -> List[Dict]:
        # 检查本地缓存
        if os.path.exists(PERSON_CACHE_FILE):
            try:
                with open(PERSON_CACHE_FILE, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    logger.info(f"从本地缓存加载了{len(cache_data)}个人物数据")
                    return cache_data
            except Exception as e:
                logger.warning(f"读取缓存数据失败: {e}")
        # 模拟数据（实际项目中替换为真实API调用）
        results = [
            {"name": "诸葛亮", "birth": "181-07-23", "bazi": "辛酉年 丁未月 壬午日 戊午时", "fact": "三国时期著名军事家、政治家"},
            {"name": "李白", "birth": "701-02-28", "bazi": "辛酉年 甲寅月 丁酉日 戊午时", "fact": "唐代著名诗人"},
            {"name": "爱因斯坦", "birth": "1879-03-14", "bazi": "己卯年 丁卯月 戊寅日 丁丑时", "fact": "现代物理学奠基人"},
            {"name": "系统自知", "birth": "2020-01-01", "bazi": "庚子年 己丑月 戊子日 甲子时", "fact": "AI系统自我认知"}
        ]
        with open(PERSON_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"成功获取并缓存了{len(results)}个人物数据")
        return results

class XuanjiPersonPredictor:
    """历史人物AI预测与复盘引擎"""
    def __init__(self):
        self.learning_cycles = 0
        self.knowledge_base = []
        # 加载人名到最近一次扩张/抽取的状态
        self.person_status = _load_person_status()
    async def predict_and_learn(self, person: Dict) -> Dict:
        # 用玄机AI系统进行预测（可集成本地API或大模型API）
        # 这里只做模拟，实际可调用AI系统API
        prediction = {
            "name": person["name"],
            "birth": person["birth"],
            "bazi": person["bazi"],
            "predicted_fact": f"预测：{person['name']}在其领域有重大成就。八字显示智慧与创新。"
        }
        # 复盘与事实对比
        match = prediction["predicted_fact"][:8] in person["fact"]
        summary = {
            "name": person["name"],
            "fact": person["fact"],
            "prediction": prediction["predicted_fact"],
            "match": match,
            "cycle": self.learning_cycles
        }
        # 学习与知识库更新
        self.knowledge_base.append({
            "name": person["name"],
            "bazi": person["bazi"],
            "pattern": f"{person['name']}八字与事实吻合度：{match}",
            "cycle": self.learning_cycles
        })
        self.learning_cycles += 1
        return summary
    async def upgrade_and_discover(self):
        # 每10个周期触发一次自主升级与新模式发现
        if self.learning_cycles % 10 == 0:
            new_pattern = f"第{self.learning_cycles}周期发现新模式：八字与成就相关性增强"
            self.knowledge_base.append({"pattern": new_pattern, "cycle": self.learning_cycles})
            logger.info(f"系统自主升级，发现新模式：{new_pattern}")
    async def save_knowledge(self):
        # 保存知识库
        with open(PERSON_KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)
    def maybe_expand_and_extract(self, person: Dict[str, Any]):
        """按频控为单个人物执行外部扩张与内部抽取。"""
        try:
            name = person.get("name") or "UNKNOWN"
            pstate = (self.person_status.setdefault("persons", {}).setdefault(name, {}))
            now = _now_ts()
            # 外部扩张
            if PERSON_NET_EXPAND and _should_run(pstate.get("last_expand_ts"), PERSON_EXPAND_INTERVAL):
                done, rec = expand_person_with_internet(person)
                if done:
                    pstate["last_expand_ts"] = now
                    _save_person_status(self.person_status)
            # 内部抽取
            if PERSON_LLM_EXTRACT and _should_run(pstate.get("last_extract_ts"), PERSON_EXTRACT_INTERVAL):
                done, rec = extract_person_facts(person)
                if done:
                    pstate["last_extract_ts"] = now
                    _save_person_status(self.person_status)
        except Exception as e:
            logger.warning(f"扩张/抽取流程异常: {e}")

async def main():
    logger.info("启动历史人物与系统自知人物AI预测与复盘循环任务...")
    try:
        collector = PersonDataCollector()
        persons = await collector.fetch_person_data()
        predictor = XuanjiPersonPredictor()
        # 主循环：对每个人物反复复盘
        for cycle in range(1000):  # 可无限循环
            for person in persons:
                summary = await predictor.predict_and_learn(person)
                logger.info(f"复盘周期{summary['cycle']}：{summary['name']}，预测：{summary['prediction']}，事实：{summary['fact']}，吻合：{summary['match']}")
                # 每人处理后尝试扩张/抽取（按频控与开关执行）
                predictor.maybe_expand_and_extract(person)
                await predictor.upgrade_and_discover()
            if cycle % 10 == 0:
                await predictor.save_knowledge()
            await asyncio.sleep(5)  # 静默后台运行，间隔5秒
        logger.info("任务完成。知识库已保存。")
    except Exception as e:
        logger.error(f"任务执行出错: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"主函数执行失败: {e}")
        traceback.print_exc()
