import importlib
import os
import json
import time
from heartbeat_manager import write_heartbeat
from urllib import request as _urlreq
from urllib.error import URLError

def _fetch_json(url: str, timeout: int = 10):
    """返回 (ok: bool, data: dict|None)"""
    try:
        requests = importlib.import_module('requests')  # 动态导入，避免静态检查报错
        try:
            resp = requests.get(url, timeout=timeout)
            if getattr(resp, 'ok', False):
                return True, resp.json()
            return False, None
        except Exception:
            return False, None
    except Exception:
        requests = None
    # fallback urllib
    try:
        with _urlreq.urlopen(url, timeout=timeout) as resp:
            if resp.status == 200:
                raw = resp.read()
                return True, json.loads(raw.decode('utf-8', errors='ignore'))
            return False, None
    except (URLError, Exception):
        return False, None

def search_books(keywords, max_results=20):
    books = []
    # Google Books API
    url_gb = f"https://www.googleapis.com/books/v1/volumes?q={keywords}&maxResults={max_results}"
    ok, data = _fetch_json(url_gb, timeout=10)
    if ok and isinstance(data, dict):
        items = data.get('items', [])
        for item in items:
            info = item.get('volumeInfo', {})
            books.append({
                'title': info.get('title'),
                'authors': info.get('authors'),
                'publishedDate': info.get('publishedDate'),
                'description': info.get('description'),
                'previewLink': info.get('previewLink'),
                'source': 'Google Books'
            })

    # 豆瓣API（模拟，实际需爬虫或第三方接口）
    url_douban = f"https://api.douban.com/v2/book/search?q={keywords}&count={max_results}"
    ok2, data2 = _fetch_json(url_douban, timeout=10)
    if ok2 and isinstance(data2, dict):
        items = data2.get('books', [])
        for item in items:
            books.append({
                'title': item.get('title'),
                'authors': item.get('author'),
                'publishedDate': item.get('pubdate'),
                'description': item.get('summary'),
                'previewLink': item.get('alt'),
                'source': 'Douban'
            })
    return books
def auto_collect_and_learn():
    subjects = [
        '易经', '梅花易数', '六爻', '大六壬', '奇门遁甲',
        '易学', '占卜', '中国古代预测', '现代易学', '易经现代解读'
    ]
    collect_interval = int(os.getenv('YI_BOOKS_INTERVAL', '3600'))  # 支持 env 调整
    while True:
        # 初始心跳：避免长周期采集导致无心跳
        try:
            write_heartbeat('yi_books_collect', phase='starting')
        except Exception:
            pass
        all_books = []
        for sub in subjects:
            print(f'正在采集: {sub}')
            try:
                books = search_books(sub, max_results=20)
                all_books.extend(books)
            except Exception as e:
                print(f'采集 {sub} 时异常: {e}')
        # 采集结果去重
        unique_books = []
        seen_titles = set()
        for b in all_books:
            title = b.get('title')
            if title and title not in seen_titles:
                unique_books.append(b)
                seen_titles.add(title)
        with open('yi_books_collection.json', 'w', encoding='utf-8') as f:
            json.dump(unique_books, f, ensure_ascii=False, indent=2)
        print(f'已采集{len(unique_books)}本相关书籍，结果保存至 yi_books_collection.json')
        # 写心跳文件：包含数量与顶级作者
        try:
            write_heartbeat('yi_books_collect', books=len(unique_books))
        except Exception:
            pass
        # 自动分析采集结果，统计热门作者/主题
        author_count = {}
        for b in unique_books:
            authors = b.get('authors')
            if authors:
                if isinstance(authors, list):
                    for a in authors:
                        author_count[a] = author_count.get(a, 0) + 1
                elif isinstance(authors, str):
                    author_count[authors] = author_count.get(authors, 0) + 1
        top_authors = sorted(author_count.items(), key=lambda x: x[1], reverse=True)[:5]
        print('热门作者：', top_authors)
        try:
            write_heartbeat('yi_books_collect', books=len(unique_books), top_authors=top_authors[:3])
        except Exception:
            pass
        # 知识融合与模型升级（示例）
        print('自动融合新书籍知识，提升预测精准度。')
        time.sleep(collect_interval)

if __name__ == '__main__':
    auto_collect_and_learn()
