#!/usr/bin/env python3
"""
HumanGate helper: pause workflow until an approval file is touched or timeout.
Intended for CI scripts to wait for human approval during dangerous operations.
"""
import argparse
import os
import time


def wait_for_approval(flag_file, timeout=3600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if os.path.exists(flag_file):
            print('approved by presence of', flag_file)
            return True
        print('waiting for approval, checking again in 10s...')
        time.sleep(10)
    print('timeout waiting for approval')
    return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--flag-file', default='/tmp/ci_human_approve')
    p.add_argument('--timeout', type=int, default=3600)
    args = p.parse_args()
    ok = wait_for_approval(args.flag_file, args.timeout)
    if not ok:
        raise SystemExit('approval timeout')


if __name__ == '__main__':
    main()
