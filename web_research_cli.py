#!/usr/bin/env python3
import sys
from internet_research import research_and_summarize

def main():
    if len(sys.argv) < 2:
        print("用法: web_research_cli.py '联网查询: 主题' 或 'url: https://example.com'")
        sys.exit(1)
    query = sys.argv[1]
    res = research_and_summarize(query, max_results=3)
    print("=== 摘要 ===")
    print(res.get('summary',''))
    print("\n=== 引用 ===")
    for u in res.get('sources',[]):
        print(u)

if __name__ == '__main__':
    main()
