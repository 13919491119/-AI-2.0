#!/usr/bin/env python3
"""知识摄取管线（初版）
读取 yi_books_collection.json ，抽取：
 - 主题关键词（基于 title + description 的简单分词与频次）
 - 作者出现次数 Top N
 - 生成简要汇总写入 knowledge_ingest_summary.json
可由守护进程定期调用，也可手动运行。
"""
import json, os, re, math, time
from collections import Counter

SRC = 'yi_books_collection.json'
OUT = 'knowledge_ingest_summary.json'
STOP = set(['的','与','和','及','在','中','上','下','了','是','本','对','以','为','与','之','用','到','这','那','也','都','可','更','不','太','很'])
TOKEN_RE = re.compile(r'[\u4e00-\u9fa5]{1,}|[0-9A-Za-z]{2,}')


def load_books(path):
    if not os.path.exists(path):
        return []
    with open(path,'r',encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return []

def tokenize(text: str):
    tokens = TOKEN_RE.findall(text or '')
    out = []
    for t in tokens:
        t = t.strip().lower()
        if not t or t in STOP or len(t) < 2:
            continue
        out.append(t)
    return out

def build_summary(books):
    author_counter = Counter()
    token_counter = Counter()
    for b in books:
        authors = b.get('authors')
        if isinstance(authors, list):
            for a in authors:
                if a:
                    author_counter[a] += 1
        elif isinstance(authors, str):
            author_counter[authors] += 1
        text = (b.get('title','') or '') + ' ' + (b.get('description','') or '')
        for tk in tokenize(text):
            token_counter[tk] += 1
    top_authors = author_counter.most_common(10)
    top_tokens = token_counter.most_common(30)
    # 粗略主题：选前若干高频词按频次平方根分层
    topics = []
    for word, freq in top_tokens[:15]:
        score = round(math.sqrt(freq),2)
        topics.append({'keyword': word,'score': score,'raw_freq': freq})
    summary = {
        'timestamp': time.time(),
        'total_books': len(books),
        'top_authors': top_authors,
        'topics': topics,
        'top_tokens': top_tokens,
    }
    return summary

def main():
    books = load_books(SRC)
    if not books:
        print('[knowledge_ingest] 无书籍数据，跳过')
        return
    summary = build_summary(books)
    with open(OUT,'w',encoding='utf-8') as f:
        json.dump(summary,f,ensure_ascii=False,indent=2)
    print(f"[knowledge_ingest] 已生成 {OUT} (books={summary['total_books']})")

if __name__=='__main__':
    main()
