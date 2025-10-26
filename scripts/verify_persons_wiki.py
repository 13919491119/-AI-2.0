"""
维基百科校验脚本：自动校验 reports/persons_deepseek.jsonl 中人物的出生日期和主要成就。
结果写入 reports/persons_verified.jsonl。
"""
import requests
import json
import time
from urllib.parse import quote

INPUT = 'reports/persons_deepseek.jsonl'
OUTPUT = 'reports/persons_verified.jsonl'

WIKI_API = 'https://zh.wikipedia.org/w/api.php'


def fetch_wiki_summary(name):
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'extracts|pageprops',
        'exintro': True,
        'explaintext': True,
        'titles': name
    }
    try:
        resp = requests.get(WIKI_API, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            if 'extract' in page:
                return page['extract']
    except Exception as e:
        return f'获取失败: {e}'
    return ''

def verify_person(person):
    wiki = fetch_wiki_summary(person['姓名'])
    result = dict(person)
    result['wiki_summary'] = wiki
    # 简单校验出生日期
    if person['出生年月日'] and person['出生年月日'][:4].isdigit():
        year = person['出生年月日'][:4]
        if year in wiki:
            result['birth_verified'] = True
        else:
            result['birth_verified'] = False
    else:
        result['birth_verified'] = False
    # 校验主要成就关键词
    if person['主要成就'] and any(k in wiki for k in person['主要成就'].split('，')):
        result['achievement_verified'] = True
    else:
        result['achievement_verified'] = False
    return result

def main():
    with open(INPUT, encoding='utf-8') as f, open(OUTPUT, 'w', encoding='utf-8') as out:
        for line in f:
            person = json.loads(line)
            verified = verify_person(person)
            out.write(json.dumps(verified, ensure_ascii=False) + '\n')
            time.sleep(0.5)  # 防止请求过快被限流
    print(f'已校验并写入 {OUTPUT}')

if __name__ == '__main__':
    main()
