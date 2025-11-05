#!/usr/bin/env python3
"""
Poll a metrics endpoint and trigger a rollback when thresholds are breached.
This is a template: real deployment systems should integrate with alerts and CD systems.
"""
import argparse
import json
import time
import requests


def load_thresholds(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_metrics(metrics, thresholds):
    # simple rule: if any metric worse than threshold -> breach
    for k, v in thresholds.items():
        val = metrics.get(k)
        if val is None:
            continue
        if isinstance(v, dict):
            if 'max' in v and val > v['max']:
                return True, f"{k} > {v['max']} ({val})"
            if 'min' in v and val < v['min']:
                return True, f"{k} < {v['min']} ({val})"
        else:
            if val > v:
                return True, f"{k} > {v} ({val})"
    return False, ''


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--canary-endpoint', required=True)
    p.add_argument('--threshold-file', required=True)
    p.add_argument('--interval', type=int, default=30)
    args = p.parse_args()

    thresholds = load_thresholds(args.threshold_file)
    print('Loaded thresholds:', thresholds)
    while True:
        try:
            r = requests.get(args.canary_endpoint, timeout=5)
            metrics = r.json()
        except Exception as e:
            print('metrics fetch error:', e)
            time.sleep(args.interval)
            continue
        breached, reason = check_metrics(metrics, thresholds)
        if breached:
            print('BREACH detected:', reason)
            # placeholder: call CD system to rollback
            print('Triggering rollback (placeholder)')
            # e.g., kubectl rollout undo deployment/foo -n canary
            return
        print('OK metrics:', metrics)
        time.sleep(args.interval)


if __name__ == '__main__':
    main()
