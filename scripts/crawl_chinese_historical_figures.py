"""
自动化爬取中国历史人物数据脚本
优先使用维基百科、百度百科等公开渠道，整理为json格式，目标100+人物。
"""
import requests
import random
import json
from bs4 import BeautifulSoup

# 维基百科中国历史人物条目（示例入口）
WIKI_LIST_URL = "https://zh.wikipedia.org/wiki/Category:%E4%B8%AD%E5%9B%BD%E5%8F%B2%E4%B8%8A%E4%BA%BA%E7%89%A9"

# 结果保存路径
import argparse
OUTPUT_PATH = "../person_data_crawled.json"  # 默认路径，后续可被参数覆盖


def get_random_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/15.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 Version/15.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 Chrome/56.0.2924.87 Safari/537.36"
    ]
    return {"User-Agent": random.choice(user_agents)}

def crawl_wikipedia_person_list(entry_url=None, max_retry=3, proxy=None):
    url = entry_url if entry_url else WIKI_LIST_URL
    for attempt in range(max_retry):
        try:
            headers = get_random_headers()
            proxies = {"http": proxy, "https": proxy} if proxy else None
            res = requests.get(url, timeout=15, headers=headers, proxies=proxies)
            res.raise_for_status()
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            # 适配新版维基百科分类页面结构
            persons = []
            # 1. 先找所有 .mw-category-group
            groups = soup.select('.mw-category-group')
            for group in groups:
                items = group.select('ul li a')
                for item in items:
                    name = item.text.strip()
                    link = "https://zh.wikipedia.org" + item.get('href')
                    persons.append({"name": name, "wiki_url": link})
            # 2. 若未找到，尝试新版结构：.mw-category-generated ul li a
            if not persons:
                items = soup.select('.mw-category-generated ul li a')
                for item in items:
                    name = item.text.strip()
                    link = "https://zh.wikipedia.org" + item.get('href')
                    persons.append({"name": name, "wiki_url": link})
            print(f"[INFO] 解析到 {len(persons)} 位历史人物条目")
            return persons
        except Exception as e:
            print(f"[WARN] 第{attempt+1}次获取人物列表失败: {e}")
    print(f"[ERROR] 获取人物列表失败，重试{max_retry}次后放弃")
    return []


def crawl_person_details(persons, max_count=120):
    results = []
    for i, person in enumerate(persons):
        if i >= max_count:
            break
        url = person["wiki_url"]
        for attempt in range(3):
            try:
                headers = get_random_headers()
                res = requests.get(url, timeout=15, headers=headers)
                res.raise_for_status()
                res.encoding = 'utf-8'
                soup = BeautifulSoup(res.text, 'html.parser')
                # 优先提取infobox后的首段简介
                summary = ""
                # 1. 先找第一个有内容的<p>标签
                p_tags = soup.select('p')
                for p in p_tags:
                    txt = p.text.strip()
                    if txt and len(txt) > 20:
                        summary = txt
                        break
                # 2. 若未找到，尝试新版结构：.mw-parser-output > p
                if not summary:
                    p_tags = soup.select('.mw-parser-output > p')
                    for p in p_tags:
                        txt = p.text.strip()
                        if txt and len(txt) > 20:
                            summary = txt
                            break
                results.append({
                    "name": person["name"],
                    "wiki_url": url,
                    "summary": summary
                })
                print(f"[OK] {person['name']} | {summary[:30]}...")
                break
            except Exception as e:
                print(f"[WARN] {person['name']} 第{attempt+1}次获取失败: {e}")
                if attempt == 2:
                    results.append({
                        "name": person["name"],
                        "wiki_url": url,
                        "summary": "获取失败: " + str(e)
                    })
    return results



def main():
    parser = argparse.ArgumentParser(description="自动化爬取中国历史人物数据，优先维基百科")
    parser.add_argument('--count', type=int, default=100, help='抓取人物数量')
    parser.add_argument('--output', type=str, default='reports/persons_enriched.jsonl', help='输出文件路径')
    parser.add_argument('--entry', type=str, default=WIKI_LIST_URL, help='入口页面URL')
    parser.add_argument('--proxy', type=str, default=None, help='代理地址（如 http://127.0.0.1:7890）')
    args = parser.parse_args()

    persons = crawl_wikipedia_person_list(entry_url=args.entry, proxy=args.proxy)
    details = crawl_person_details(persons, max_count=args.count)
    # 输出为jsonl格式
    with open(args.output, 'w', encoding='utf-8') as f:
        for item in details:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"已保存 {len(details)} 条历史人物数据到 {args.output}")

if __name__ == "__main__":
    main()
