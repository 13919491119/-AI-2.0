#!/usr/bin/env python3
"""轻量 HTTP 健康检查服务器（无外部依赖）。
提供：
  GET /health -> 200/503 简单 up/down
  GET /status -> JSON 输出 ai_meta_status.get_status()

默认绑定 localhost:5001，可通过环境变量 AI_HEALTH_HOST/AI_HEALTH_PORT 配置。
"""
import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver
import threading

import ai_meta_status

HOST = os.getenv('AI_HEALTH_HOST', '127.0.0.1')
PORT = int(os.getenv('AI_HEALTH_PORT', '5001'))


class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ('/', '/health'):
            status = ai_meta_status.get_status()
            up = status['ai_meta_system']['running'] and status['autonomous_run']['running']
            code = 200 if up else 503
            self._send_json({'up': up}, code=code)
            return
        if self.path == '/status':
            status = ai_meta_status.get_status()
            code = 200
            self._send_json(status, code=code)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        # 避过默认 stderr 打印，主程序已经在收集日志
        return


def run_server(host=HOST, port=PORT):
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"[ai_meta_health] listening on http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except Exception:
        pass


def start_in_thread(host=HOST, port=PORT):
    t = threading.Thread(target=run_server, args=(host, port), daemon=True)
    t.start()
    return t


if __name__ == '__main__':
    run_server()
