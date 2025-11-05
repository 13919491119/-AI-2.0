#!/usr/bin/env python3
"""
Simple A/B test runner stub: dispatches requests to A/B endpoints and aggregates basic metrics.
This is a template to be adapted to your routing/infrastructure.
"""
import argparse
import requests
import time
from collections import defaultdict


def run_test(a_url, b_url, n=100):
    stats = defaultdict(list)
    for i in range(n):
        for label, url in [('A', a_url), ('B', b_url)]:
            try:
                t0 = time.time()
                r = requests.get(url, timeout=3)
                dt = (time.time()-t0)*1000
                stats[label].append({'status': r.status_code, 'lat_ms': dt})
            except Exception as e:
                stats[label].append({'status': 'err', 'lat_ms': None})
    return stats


def summary(stats):
    out = {}
    for k, arr in stats.items():
        ok = sum(1 for x in arr if x['status']==200)
        latency = [x['lat_ms'] for x in arr if x['lat_ms'] is not None]
        out[k] = {'count': len(arr), 'ok': ok, 'p95_latency_ms': (sorted(latency)[int(len(latency)*0.95)] if latency else None)}
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--a')
    p.add_argument('--b')
    p.add_argument('--requests', type=int, default=50)
    args = p.parse_args()
    stats = run_test(args.a, args.b, n=args.requests)
    print(summary(stats))


if __name__ == '__main__':
    main()
