#!/usr/bin/env python3
"""
system_check.py
系统自检脚本 - 自动检测所有服务状态并生成诊断报告
"""
import requests
import subprocess
import sys
from datetime import datetime

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def check_service(name, url, timeout=3):
    """检查服务状态"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"{Colors.GREEN}✅ {name}: 运行正常{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}❌ {name}: 状态码 {response.status_code}{Colors.RESET}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}❌ {name}: 无法连接 ({str(e)[:50]}...){Colors.RESET}")
        return False

def check_process(name, process_name):
    """检查进程是否运行"""
    try:
        result = subprocess.run(['pgrep', '-f', process_name], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"{Colors.GREEN}✅ {name}: 运行中 (PID: {', '.join(pids)}){Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}❌ {name}: 未运行{Colors.RESET}")
            return False
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  {name}: 检查失败 ({e}){Colors.RESET}")
        return False

def main():
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}🔍 玄机AI系统自检开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    results = {}
    
    # 检查核心API服务
    print(f"{Colors.BLUE}【核心服务检查】{Colors.RESET}")
    results['api'] = check_service("API服务 (8000端口)", "http://127.0.0.1:8000/health")
    
    # 检查报告前端服务
    print(f"\n{Colors.BLUE}【报告服务检查】{Colors.RESET}")
    results['report'] = check_service("报告前端 (8080端口)", "http://127.0.0.1:8080/report")
    
    # 检查微信集成服务
    print(f"\n{Colors.BLUE}【微信集成检查】{Colors.RESET}")
    results['wechat'] = check_service("微信服务 (8088端口)", "http://127.0.0.1:8088/health")
    
    # 检查进程
    print(f"\n{Colors.BLUE}【进程检查】{Colors.RESET}")
    results['api_process'] = check_process("API进程", "celestial_nexus.api")
    results['report_process'] = check_process("报告进程", "report_frontend.py")
    results['wechat_process'] = check_process("微信进程", "wechat_server.py")
    
    # 生成总结报告
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}📊 自检结果总结{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\n总检查项: {total}")
    print(f"{Colors.GREEN}通过: {passed}{Colors.RESET}")
    print(f"{Colors.RED}失败: {failed}{Colors.RESET}")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}🎉 系统状态良好，所有服务运行正常！{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠️  发现 {failed} 个问题，请检查相关服务{Colors.RESET}")
        print(f"\n{Colors.BLUE}💡 修复建议：{Colors.RESET}")
        print("  1. 运行 bash start_all.sh 启动核心服务")
        print("  2. 运行 bash setup_wechat_integration.sh 启动微信服务")
        print("  3. 检查日志文件: api_server.log, report_frontend.log, wechat_server.log")
        return 1

if __name__ == "__main__":
    sys.exit(main())
