"""
审批 CLI：对 upgrade_plan_pending.json 进行人工批准或拒绝
用法：
  python3 tools/approve_upgrade.py --approve --approver "Alice"
  python3 tools/approve_upgrade.py --reject --approver "Alice" --reason "need more tests"
"""
import argparse
import json
import os
from datetime import datetime

PENDING = 'upgrade_plan_pending.json'
APPROVED = 'upgrade_plan_approved.json'
REJECTED = 'upgrade_plan_rejected.json'


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--approve', action='store_true')
    group.add_argument('--reject', action='store_true')
    parser.add_argument('--approver', type=str, required=True)
    parser.add_argument('--reason', type=str, default='')
    args = parser.parse_args()

    if not os.path.exists(PENDING):
        print(f"待审批文件 {PENDING} 不存在")
        return
    with open(PENDING, 'r', encoding='utf-8') as f:
        data = json.load(f)

    now = datetime.now().isoformat()
    if args.approve:
        out = {
            'approved_at': now,
            'approver': args.approver,
            'plan': data.get('plan'),
            'mode': data.get('mode', 'dry-run'),
            'status': 'approved'
        }
        with open(APPROVED, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"已批准，写入 {APPROVED}")
    else:
        out = {
            'rejected_at': now,
            'approver': args.approver,
            'plan': data.get('plan'),
            'status': 'rejected',
            'reason': args.reason
        }
        with open(REJECTED, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"已拒绝，写入 {REJECTED}")

if __name__ == '__main__':
    main()
