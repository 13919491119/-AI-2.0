#!/usr/bin/env python3
"""
微信公众号与 Celestial Nexus AI 系统对接服务
公众号: 刘洪鹏76
"""
from flask import Flask, request, make_response, jsonify
import requests
import xml.etree.ElementTree as ET
import time
import json
import os
import logging
import hashlib
from typing import List, Optional, Tuple, Deque
from collections import deque

from wechat_crypto import build_crypto_from_env, WeChatCrypto
from activation_persistence import (
    activate as persistent_activate,
    is_activated as persistent_is_activated,
    is_activation_phrase as persistent_is_activation_phrase,
    welcome_menu as persistent_welcome_menu,
    map_shortcut as persistent_map_shortcut
)

# Prometheus metrics (lazy fallback if not installed)
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
except ImportError:  # minimal fallback
    Counter = Histogram = None  # type: ignore
    def generate_latest():  # type: ignore
        return b''
    CONTENT_TYPE_LATEST = 'text/plain'

# 尝试导入 pyngrok，如未安装则优雅降级
try:
    from pyngrok import ngrok  # type: ignore
except ImportError:
    ngrok = None
    NGROK_IMPORT_ERROR = True
else:
    NGROK_IMPORT_ERROR = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('wechat_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============ 延迟公众号链接策略 ============
# 如果存在 WECHAT_LINK_PENDING.md 文件，则表示当前仅运行AI核心，不启动公众号对接服务。
PENDING_FLAG_FILE = 'WECHAT_LINK_PENDING.md'
if os.path.exists(PENDING_FLAG_FILE) and os.environ.get('FORCE_WECHAT_LINK','0') != '1':
    logger.warning(
        '\n[延迟启动] 检测到 %s ，当前暂不启动微信公众号对接服务。\n'
        '若需立即连接公众号：\n'
        '  1) 删除该文件 rm %s\n'
        '  2) 或设置环境变量 FORCE_WECHAT_LINK=1 重新运行\n'
        '  3) 然后执行 ./start_wechat_gunicorn.sh 或 python wechat_server.py\n',
        PENDING_FLAG_FILE, PENDING_FLAG_FILE
    )
    # 直接退出，不加载Flask路由（保持安全）
    import sys as _sys
    _sys.exit(0)

app = Flask(__name__)

# Metrics definitions
if Counter and Histogram:
    METRICS_ENABLED = True
    REQ_TOTAL = Counter('wechat_requests_total', 'Total WeChat requests', ['method','type'])
    REQ_LATENCY = Histogram('wechat_request_latency_seconds', 'Latency of WeChat handling', ['type'])
    DEDUP_HITS = Counter('wechat_dedup_hits_total', 'Deduplicated incoming messages')
    SIGNATURE_FAIL = Counter('wechat_signature_fail_total', 'Signature verification failures')
    ORIGINAL_ID_MISMATCH = Counter('wechat_original_id_mismatch_total', 'Original ID(ToUserName) mismatch count')
    RATE_LIMIT_HITS = Counter('wechat_rate_limit_hits_total', 'Rate limit hit count')
    ACTIVATION_TOTAL = Counter('wechat_activation_total', 'Session activation count')
    DEACTIVATION_TOTAL = Counter('wechat_deactivation_total', 'Session deactivation count')
    API_FAIL_TOTAL = Counter('wechat_api_fail_total', 'Backend API total failure count')
    SHORTCUT_TOTAL = Counter('wechat_shortcut_total', 'Numeric or keyword shortcut usage', ['key'])
    SESSION_EXPIRED_TOTAL = Counter('wechat_session_expired_total', 'Session expired count')
else:
    METRICS_ENABLED = False
    # 备用占位，防止引用未定义
    REQ_TOTAL = REQ_LATENCY = DEDUP_HITS = SIGNATURE_FAIL = ORIGINAL_ID_MISMATCH = RATE_LIMIT_HITS = None  # type: ignore

# Optional Redis client for cross-process dedup
REDIS_URL = os.environ.get('WECHAT_REDIS_URL')
_redis_client = None
if REDIS_URL:
    try:
        import redis  # type: ignore
        _redis_client = redis.Redis.from_url(REDIS_URL)
        _redis_client.ping()
        logger.info(f"已启用Redis去重: {REDIS_URL}")
    except Exception as e:  # pragma: no cover
        logger.error(f"Redis初始化失败，回退内存去重: {e}")
        _redis_client = None

# Simple in-memory dedup (sliding window)
DEDUP_WINDOW_SECONDS = int(os.environ.get('WECHAT_DEDUP_WINDOW', '120'))
DEDUP_MAX_SIZE = int(os.environ.get('WECHAT_DEDUP_MAX', '500'))
_recent_msgs: Deque[Tuple[str,int]] = deque()  # (key, ts)
# 最近事件调试缓存 (ts, from_user, content, phase, note)
RECENT_EVENT_LIMIT = 50
_recent_events: Deque[Tuple[float,str,str,str,str]] = deque()

def _record_event(from_user: str, content: str, phase: str, note: str = ""):
    try:
        _recent_events.append((time.time(), from_user, content, phase, note))
        while len(_recent_events) > RECENT_EVENT_LIMIT:
            _recent_events.popleft()
    except Exception:
        pass

# 简易速率限制 (每 from_user 每分钟最大消息数) - 可选 Redis 支持
RATE_LIMIT_PER_MIN = int(os.environ.get('WECHAT_RATE_LIMIT_PER_MIN', '0'))  # 0 表示禁用
_rate_window: dict[str, Tuple[int,int]] = {}  # user -> (window_start_ts, count)

def _rate_limited(user: str) -> bool:
    if RATE_LIMIT_PER_MIN <= 0:
        return False
    now = int(time.time())
    minute = now // 60
    if _redis_client:
        key = f"wechat_rl:{user}:{minute}"
        # 使用INCR + EXPIRE
        try:
            val = _redis_client.incr(key)
            if val == 1:
                _redis_client.expire(key, 120)
            if val > RATE_LIMIT_PER_MIN:
                if METRICS_ENABLED:
                    RATE_LIMIT_HITS.inc()
                return True
            return False
        except Exception:
            # 回退本地
            pass
    win, cnt = _rate_window.get(user, (minute, 0))
    if win != minute:
        win, cnt = minute, 0
    cnt += 1
    _rate_window[user] = (win, cnt)
    if cnt > RATE_LIMIT_PER_MIN:
        if METRICS_ENABLED:
            RATE_LIMIT_HITS.inc()
        return True
    return False

def _dedup_key(from_user: str, msg_id: Optional[str], content: Optional[str]) -> str:
    base = f"{from_user}:{msg_id or ''}:{content or ''}"
    return hashlib.sha1(base.encode()).hexdigest()

def check_and_remember(from_user: str, msg_id: Optional[str], content: Optional[str]) -> bool:
    now = int(time.time())
    key = _dedup_key(from_user, msg_id, content)
    # Redis path
    if _redis_client:
        ttl = DEDUP_WINDOW_SECONDS
        existed = _redis_client.set(name=f"wechat_dedup:{key}", value=1, nx=True, ex=ttl)
        if not existed:
            if METRICS_ENABLED:
                DEDUP_HITS.inc()
            return True
        return False
    # purge expired
    cutoff = now - DEDUP_WINDOW_SECONDS
    while _recent_msgs and _recent_msgs[0][1] < cutoff:
        _recent_msgs.popleft()
    for k, _ in _recent_msgs:
        if k == key:
            if METRICS_ENABLED:
                DEDUP_HITS.inc()
            return True
    _recent_msgs.append((key, now))
    if len(_recent_msgs) > DEDUP_MAX_SIZE:
        _recent_msgs.popleft()
    return False

# 配置
CELESTIAL_API = 'http://localhost:8000'
# 备用端点（多服务并存容错）可通过环境变量 WECHAT_API_FALLBACKS 逗号分隔覆盖
API_FALLBACKS = [u.strip() for u in os.environ.get('WECHAT_API_FALLBACKS','http://localhost:8000,http://127.0.0.1:8000').split(',') if u.strip()]
PORT = int(os.environ.get('WECHAT_PORT', 9090))  # 改为9090端口避免冲突
USE_NGROK = os.environ.get('USE_NGROK', 'true').lower() == 'true'

# 微信公众号信息 & Token 配置（支持环境变量覆盖与多 Token 迁移期兼容）
WECHAT_NAME = os.environ.get('WECHAT_NAME', '刘洪鹏76')
WECHAT_ORIGINAL_ID = os.environ.get('WECHAT_ORIGINAL_ID', '').strip()  # gh_ 开头原始ID
STRICT_ORIGINAL_ID = os.environ.get('STRICT_ORIGINAL_ID', '0') == '1'
PRIMARY_TOKEN = os.environ.get('WECHAT_TOKEN', 'celestial_nexus_ai_token').strip()
EXTRA_TOKENS_RAW = os.environ.get('WECHAT_ACCEPT_TOKENS', '')  # 兼容老Token: 以逗号分隔
EXTRA_TOKENS: List[str] = [t.strip() for t in EXTRA_TOKENS_RAW.split(',') if t.strip()]
ALL_TOKENS: List[str] = [PRIMARY_TOKEN] + [t for t in EXTRA_TOKENS if t != PRIMARY_TOKEN]

STRICT_VERIFY = os.environ.get('STRICT_WECHAT_VERIFY', '1') == '1'  # 严格模式下签名不匹配不返回 echostr

CRYPTO: Optional[WeChatCrypto] = build_crypto_from_env()
if CRYPTO:
    logger.info("检测到安全模式配置，将尝试处理加密消息")
else:
    logger.info("未启用安全模式(未设置 WECHAT_ENCODING_AES_KEY / WECHAT_APPID) - 使用明文模式")

def compute_signature(token: str, timestamp: str, nonce: str) -> str:
    """按微信规范计算签名"""
    elements = [token, timestamp, nonce]
    elements.sort()
    raw = ''.join(elements)
    return hashlib.sha1(raw.encode('utf-8')).hexdigest()

def verify_signature(signature: str, timestamp: str, nonce: str) -> bool:
    """尝试所有已配置 Token，任一匹配即通过"""
    for idx, token in enumerate(ALL_TOKENS):
        sign = compute_signature(token, timestamp, nonce)
        if sign == signature:
            if idx == 0:
                logger.info("签名验证成功(主Token)")
            else:
                logger.warning(f"签名验证成功(兼容Token第{idx}个) 建议尽快在公众号后台更新为主Token")
            return True
    return False

@app.get('/metrics')
def metrics():
    if not METRICS_ENABLED:
        return 'metrics disabled (prometheus-client not installed)', 503
    data = generate_latest()
    resp = make_response(data)
    resp.headers['Content-Type'] = CONTENT_TYPE_LATEST
    return resp

@app.get('/health')
def health():  # 简单健康探针
    return jsonify({
        'status': 'ok',
        'wechat_port': PORT,
        'use_ngrok': USE_NGROK,
        'strict_verify': STRICT_VERIFY,
        'tokens': len(ALL_TOKENS),
        'wechat_name': WECHAT_NAME,
        'original_id': WECHAT_ORIGINAL_ID or None,
        'strict_original_id': STRICT_ORIGINAL_ID,
    })

@app.get('/_recent')
def recent():
    # 简易调试端点，限制本地访问
    if request.remote_addr not in ('127.0.0.1', '::1'):
        return jsonify({'error':'forbidden'}), 403
    out = []
    for ts, u, c, ph, note in list(_recent_events)[-RECENT_EVENT_LIMIT:]:
        out.append({
            'ts': ts,
            'time': time.strftime('%H:%M:%S', time.localtime(ts)),
            'user': u,
            'content': c,
            'phase': ph,
            'note': note
        })
    return jsonify({'recent': out, 'count': len(out)})

@app.get('/_debug_signature')
def debug_signature():  # 仅本地调试用
    if request.remote_addr not in ('127.0.0.1', '::1'):
        return "forbidden", 403
    ts = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    if not (ts and nonce):
        return jsonify({'error': 'need timestamp & nonce'}), 400
    calc = compute_signature(PRIMARY_TOKEN, ts, nonce)
    return jsonify({'timestamp': ts, 'nonce': nonce, 'expected_signature': calc, 'primary_token_length': len(PRIMARY_TOKEN)})

# ===== 会话触发模式配置 =====
# 兼容旧逻辑：仍保留内存激活短语；永久激活由 activation_persistence 管理
ACTIVATION_PHRASES = [ '玄机设计与实现AI系统', '启动玄机AI', '连接玄机AI', '激活玄机AI', '启动系统' ]
DEACTIVATE_PHRASES = ['退出', '结束', '停止', 'stop', 'quit']
HELP_PHRASES = ['help', '帮助', '?', '？']
WELCOME_MESSAGE = (
    '✅ 已成功连接【玄机AI系统】\n\n'
    '指令菜单：\n'
    '1、双色球预测\n'
    '2、预测任务  (自定义需求或问题)\n'
    '3、学习成果  (查看模型学习与升级情况)\n'
    '4、系统状态  (运行/监控概览)\n'
    '\n直接输入 1~4 对应文字或完整问题，例如：\n' 
    ' - 学习成果\n - 双色球预测\n - 系统状态\n - 我想提交一个新的预测任务：XXXX\n'
    '\n发送“退出”结束，会话空闲15分钟自动失效；发送“帮助”查看指令说明。'
)

# 用户激活状态 (内存，进程级；后续可扩展Redis)
_active_users: dict[str, float] = {}
SESSION_TTL = int(os.environ.get('WECHAT_SESSION_TTL', '900'))

# Redis 会话共享（可选）键空间: wechat_session:<user>
def _redis_set_session(user: str):
    if not _redis_client:
        return
    try:
        _redis_client.setex(f"wechat_session:{user}", SESSION_TTL, int(time.time()))
    except Exception:
        pass

def _redis_check_session(user: str) -> bool:
    if not _redis_client:
        return False
    try:
        v = _redis_client.get(f"wechat_session:{user}")
        if v:
            _redis_client.expire(f"wechat_session:{user}", SESSION_TTL)
            return True
    except Exception:
        return False
    return False
SESSION_TTL = int(os.environ.get('WECHAT_SESSION_TTL', '900'))  # 15分钟无交互自动失效

def _is_active(user: str) -> bool:
    # 进程内 + Redis 共享
    ts = _active_users.get(user)
    now = time.time()
    if ts and now - ts <= SESSION_TTL:
        return True
    # 本地过期
    if ts and now - ts > SESSION_TTL:
        _active_users.pop(user, None)
        if METRICS_ENABLED:
            SESSION_EXPIRED_TOTAL.inc()
    # Redis 检查
    if _redis_check_session(user):
        return True
    return False

def _activate(user: str):
    _active_users[user] = time.time()
    _redis_set_session(user)

def _deactivate(user: str):
    _active_users.pop(user, None)

def _match_activation(text: str) -> bool:
    """判断文本是否触发激活：
    - 完全匹配激活短语
    - 文本包含任一激活短语（防止用户附加说明）
    - 用户一次发送多个短语，用 / 或 空格 分隔
    """
    base = text.strip()
    if not base:
        return False
    lowered = base.lower()
    # 分割: 允许 ' / ' 或 '/' 或 空格 作为多短语
    candidates = [c for part in base.replace(' /','/').replace('/ ','/').split('/') for c in part.split() if c]
    if not candidates:
        candidates = [base]
    act_set_exact = set(ACTIVATION_PHRASES)
    for cand in candidates:
        if cand in act_set_exact:
            return True
        for phrase in ACTIVATION_PHRASES:
            if phrase in cand or phrase.lower() in cand.lower():
                return True
    # 整体包含判断
    for phrase in ACTIVATION_PHRASES:
        if phrase in base or phrase.lower() in lowered:
            return True
    # 宽松启发式：包含“玄机设计”与“AI系统”两个关键词
    if '玄机设计' in base and 'AI系统' in base:
        return True
    return False

# 命令处理函数 (已激活状态下调用后台AI)
def handle_command(command):
    """处理用户命令并调用对应的 Celestial Nexus API"""
    try:
        last_err = None
        for base in API_FALLBACKS:
            url = f"{base.rstrip('/')}/run_xuanji_ai"
            try:
                result = requests.post(url, json={'input': command, 'source': '刘洪鹏76公众号'}, timeout=8)
                if result.status_code == 200 and 'result' in result.json():
                    response_data = result.json()
                    return response_data.get('result', '预测结果生成中，请稍后查询')
                else:
                    last_err = f"status={result.status_code} body={result.text[:120]}"
                    logger.warning(f"主/备API未成功 url={url} {last_err}")
            except Exception as ie:
                last_err = str(ie)
                logger.warning(f"请求失败 url={url} err={ie}")
        raise RuntimeError(last_err or 'all api endpoints failed')
    except Exception as e:
        logger.error(f"API调用异常(全部端点失败): {e}")
        if METRICS_ENABLED:
            API_FAIL_TOTAL.inc()
        # 本地兜底逻辑：识别常用关键词
        lower = command.lower()
        if '学习成果' in command or 'learning' in lower:
            return "[本地兜底] 学习成果功能暂时繁忙，请稍后重试。"
        if '双色球' in command:
            return "[本地兜底] 双色球预测服务暂时不可用。"
        if '系统状态' in command:
            return "[本地兜底] 系统状态获取暂时不可用。"
        return "系统暂时繁忙，请稍后再试。"
    
    # 特殊命令处理
    if command.lower() in HELP_PHRASES or command in HELP_PHRASES:
        return (
            '【玄机AI系统 - 指令帮助】\n\n'
            '核心命令：\n'
            ' - 学习成果: 查看系统最新学习/推演结果\n'
            ' - 双色球预测: 获取近期双色球号码预测\n'
            ' - 系统状态: 查看当前系统运行状态\n'
            ' - 周期报告: 获取最新运营/策略报告\n\n'
            '控制命令：\n'
            ' - 退出: 结束当前会话\n'
            ' - 帮助: 显示本帮助\n\n'
            '发送任意问题/需求，AI将尝试解析并响应。'
        )

@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    """微信公众号接口"""
    # 处理服务器验证请求
    if request.method == 'GET':
        start_ts = time.time()
        signature = request.args.get('signature', '').strip()
        timestamp = request.args.get('timestamp', '').strip()
        nonce = request.args.get('nonce', '').strip()
        echostr = request.args.get('echostr', '').strip()

        logger.info(
            "收到验证请求: signature=%s, timestamp=%s, nonce=%s, echostr(length)=%s", 
            signature, timestamp, nonce, len(echostr) if echostr else 0
        )

        if not (signature and timestamp and nonce and echostr):
            logger.warning("参数不完整: signature/timestamp/nonce/echostr 缺失")
            return "缺少必要参数", 400

        ok = verify_signature(signature, timestamp, nonce)
        if ok:
            logger.info(f"验证通过，返回 echostr (len={len(echostr)})")
            if METRICS_ENABLED:
                REQ_TOTAL.labels(method='GET', type='verify').inc()
                REQ_LATENCY.labels(type='verify').observe(time.time()-start_ts)
            return echostr
        else:
            # 调试信息（不输出真实 Token）
            debug_expected = compute_signature(PRIMARY_TOKEN, timestamp, nonce)
            logger.error(
                "签名验证失败: received=%s expected(primary)=%s 主Token长度=%d 兼容Token数量=%d", 
                signature, debug_expected, len(PRIMARY_TOKEN), len(EXTRA_TOKENS)
            )
            if METRICS_ENABLED:
                SIGNATURE_FAIL.inc()
            if STRICT_VERIFY:
                return "signature mismatch", 403
            else:
                logger.warning("非严格模式：仍返回 echostr 以便调试 —— 建议开启 STRICT_WECHAT_VERIFY=1")
                if METRICS_ENABLED:
                    REQ_TOTAL.labels(method='GET', type='verify_relaxed').inc()
                    REQ_LATENCY.labels(type='verify_relaxed').observe(time.time()-start_ts)
                return echostr
    
    # 处理微信消息
    elif request.method == 'POST':
        start_ts = time.time()
        if METRICS_ENABLED:
            REQ_TOTAL.labels(method='POST', type='incoming').inc()
        try:
            raw_body = request.data
            logger.info(f"收到消息: {raw_body[:200]}")

            encrypt_type = request.args.get('encrypt_type')
            msg_signature = request.args.get('msg_signature')
            timestamp = request.args.get('timestamp')
            nonce = request.args.get('nonce')

            # 如果开启安全模式且收到加密消息
            if CRYPTO and encrypt_type == 'aes':
                try:
                    root_enc = ET.fromstring(raw_body)
                    cipher_text = root_enc.findtext('Encrypt')
                    if not cipher_text:
                        raise ValueError('加密消息缺少 Encrypt 节点')
                    # 校验签名
                    calc_sig = CRYPTO.sign(timestamp, nonce, cipher_text)
                    if calc_sig != msg_signature:
                        logger.error("加密消息签名不匹配")
                        return "signature error", 403
                    xml_plain = CRYPTO.decrypt(cipher_text)
                    logger.info(f"解密后XML: {xml_plain[:120]}")
                    root = ET.fromstring(xml_plain)
                except Exception as e:
                    logger.error(f"加密消息处理失败: {e}")
                    return "decrypt error", 400
            else:
                # 明文模式
                root = ET.fromstring(raw_body)
            
            from_user = root.find('FromUserName').text
            to_user = root.find('ToUserName').text
            msg_type = root.find('MsgType').text

            # 原始ID校验
            if WECHAT_ORIGINAL_ID:
                if STRICT_ORIGINAL_ID and to_user != WECHAT_ORIGINAL_ID:
                    logger.error(f"原始ID不匹配: 收到ToUserName={to_user} 期望={WECHAT_ORIGINAL_ID}")
                    if METRICS_ENABLED:
                        ORIGINAL_ID_MISMATCH.inc()
                    return "original id mismatch", 403
                elif not STRICT_ORIGINAL_ID and to_user != WECHAT_ORIGINAL_ID:
                    logger.warning(f"原始ID不同(非严格模式): 收到={to_user} 配置={WECHAT_ORIGINAL_ID}")
                    if METRICS_ENABLED:
                        ORIGINAL_ID_MISMATCH.inc()
            
            # 去重与重放保护 (基于 MsgId 或内容)
            msg_id_elem = root.find('MsgId')
            msg_id = msg_id_elem.text if msg_id_elem is not None else None
            content_for_dedup = None

            # 只处理文本消息
            if msg_type == 'text':
                content = root.find('Content').text
                content_for_dedup = content
                logger.info(f"用户 {from_user} 发送: {content}")

                dedup_hit = check_and_remember(from_user, msg_id, content_for_dedup)
                if dedup_hit:
                    # 对激活类或帮助类不执行静默丢弃，继续处理，便于用户重复尝试
                    if not (_match_activation(content) or content.strip() in HELP_PHRASES):
                        logger.warning("检测到重复消息，忽略处理")
                        _record_event(from_user, content, 'dedup_skip')
                        return "success"  # WeChat 仍需200
                    else:
                        logger.info("重复激活/帮助消息仍继续处理以便用户得到反馈")
                        _record_event(from_user, content, 'dedup_continue')
                else:
                    _record_event(from_user, content, 'incoming')

                if _rate_limited(from_user):
                    logger.warning(f"用户 {from_user} 速率限制触发")
                    reply_content = "请求过于频繁，请稍后再试"
                    reply = f"""<xml>
                <ToUserName><![CDATA[{from_user}]]></ToUserName>
                <FromUserName><![CDATA[{to_user}]]></FromUserName>
                <CreateTime>{int(time.time())}</CreateTime>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA[{reply_content}]]></Content>
                </xml>"""
                    if CRYPTO and encrypt_type == 'aes':
                        enc, sig, ts_out, nonce_out = CRYPTO.encrypt(reply)
                        reply_enc = f"""<xml>
<Encrypt><![CDATA[{enc}]]></Encrypt>
<MsgSignature><![CDATA[{sig}]]></MsgSignature>
<TimeStamp>{ts_out}</TimeStamp>
<Nonce><![CDATA[{nonce_out}]]></Nonce>
</xml>"""
                        response = make_response(reply_enc)
                    else:
                        response = make_response(reply)
                    response.content_type = 'application/xml'
                    if METRICS_ENABLED:
                        REQ_LATENCY.labels(type='incoming').observe(time.time()-start_ts)
                    return response
                
                # ===== 触发模式逻辑 =====
                normalized = content.strip()
                normalized_lower = normalized.lower()

                # 退出会话
                if any(p == normalized or p.lower() == normalized_lower for p in DEACTIVATE_PHRASES):
                    if _is_active(from_user):
                        _deactivate(from_user)
                        reply_content = '会话已结束。如需再次使用，请发送 “玄机设计与实现AI系统” 重新连接。'
                    else:
                        reply_content = '当前没有激活的会话。发送 “玄机设计与实现AI系统” 以连接。'
                    _record_event(from_user, content, 'deactivate')
                # 激活会话
                elif persistent_is_activation_phrase(normalized):
                    # 激活立即返回，不调用后端
                    persistent_activate()  # 永久激活
                    _activate(from_user)   # 进程内会话保持
                    logger.info(f"ACTIVATE: user={from_user} content={normalized}")
                    if METRICS_ENABLED:
                        ACTIVATION_TOTAL.inc()
                    reply_content = persistent_welcome_menu()
                    _record_event(from_user, content, 'activate')
                    # 直接构建返回XML（提早return防止后续逻辑意外覆盖）
                    reply = f"""<xml>
                <ToUserName><![CDATA[{from_user}]]></ToUserName>
                <FromUserName><![CDATA[{to_user}]]></FromUserName>
                <CreateTime>{int(time.time())}</CreateTime>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA[{reply_content}]]></Content>
                </xml>"""
                    if CRYPTO and encrypt_type == 'aes':
                        enc, sig, ts_out, nonce_out = CRYPTO.encrypt(reply)
                        reply_enc = f"""<xml>
<Encrypt><![CDATA[{enc}]]></Encrypt>
<MsgSignature><![CDATA[{sig}]]></MsgSignature>
<TimeStamp>{ts_out}</TimeStamp>
<Nonce><![CDATA[{nonce_out}]]></Nonce>
</xml>"""
                        response = make_response(reply_enc)
                    else:
                        response = make_response(reply)
                    response.content_type = 'application/xml'
                    if METRICS_ENABLED:
                        REQ_LATENCY.labels(type='incoming').observe(time.time()-start_ts)
                    return response
                # 未激活情况下除非触发，否则提示
                elif not (_is_active(from_user) or persistent_is_activated()):
                    if any(h == normalized or h.lower() == normalized_lower for h in HELP_PHRASES):
                        reply_content = '尚未连接AI。请先发送 “玄机设计与实现AI系统” 激活，然后再发送指令。'
                    else:
                        reply_content = '未检测到激活会话。请先发送 “玄机设计与实现AI系统” 建立连接。发送“帮助”查看说明。'
                    _record_event(from_user, content, 'not_active')
                else:
                    # 已激活，刷新时间 & 进入AI处理
                    _activate(from_user)
                    mapped = persistent_map_shortcut(content)
                    if mapped:
                        if METRICS_ENABLED:
                            SHORTCUT_TOTAL.labels(key=mapped).inc()
                        reply_content = handle_command(mapped)
                    else:
                        # 预测任务解析: “预测任务:” or “task:” 前缀
                        lower_c = content.lower()
                        if lower_c.startswith('预测任务') or lower_c.startswith('预测任务:') or lower_c.startswith('task:'):
                            # 提取描述
                            desc = content.split(':',1)[1].strip() if ':' in content else content[3:].strip()
                            if not desc:
                                reply_content = '请在“预测任务:”后提供描述，如：预测任务: 分析近10期冷热分布'
                            else:
                                # 简单包装交给AI
                                reply_content = handle_command(f"预测任务 {desc}")
                        else:
                            reply_content = handle_command(content)
                    _record_event(from_user, content, 'ai_handle')
                
                # 构建回复XML
                reply = f"""<xml>
                <ToUserName><![CDATA[{from_user}]]></ToUserName>
                <FromUserName><![CDATA[{to_user}]]></FromUserName>
                <CreateTime>{int(time.time())}</CreateTime>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA[{reply_content}]]></Content>
                </xml>"""
                
                logger.info(f"回复: {reply_content[:30]}...")
                # 如果加密模式，需要再加密包装
                if CRYPTO and encrypt_type == 'aes':
                    enc, sig, ts_out, nonce_out = CRYPTO.encrypt(reply)
                    reply_enc = f"""<xml>
<Encrypt><![CDATA[{enc}]]></Encrypt>
<MsgSignature><![CDATA[{sig}]]></MsgSignature>
<TimeStamp>{ts_out}</TimeStamp>
<Nonce><![CDATA[{nonce_out}]]></Nonce>
</xml>"""
                    response = make_response(reply_enc)
                else:
                    response = make_response(reply)
                response.content_type = 'application/xml'
                if METRICS_ENABLED:
                    REQ_LATENCY.labels(type='incoming').observe(time.time()-start_ts)
                return response
            else:
                # 非文本消息回复
                reply = f"""<xml>
                <ToUserName><![CDATA[{from_user}]]></ToUserName>
                <FromUserName><![CDATA[{to_user}]]></FromUserName>
                <CreateTime>{int(time.time())}</CreateTime>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA[目前只支持文本消息，请发送文字进行预测查询]]></Content>
                </xml>"""
                if CRYPTO and encrypt_type == 'aes':
                    enc, sig, ts_out, nonce_out = CRYPTO.encrypt(reply)
                    reply_enc = f"""<xml>
<Encrypt><![CDATA[{enc}]]></Encrypt>
<MsgSignature><![CDATA[{sig}]]></MsgSignature>
<TimeStamp>{ts_out}</TimeStamp>
<Nonce><![CDATA[{nonce_out}]]></Nonce>
</xml>"""
                    response = make_response(reply_enc)
                else:
                    response = make_response(reply)
                response.content_type = 'application/xml'
                if METRICS_ENABLED:
                    REQ_LATENCY.labels(type='incoming').observe(time.time()-start_ts)
                return response
                
        except Exception as e:
            logger.error(f"处理微信消息错误: {e}")
            return "error"

def start_ngrok():
    """启动ngrok隧道服务获取公网地址 (若失败返回本地地址)"""
    if ngrok is None:
        logger.warning("pyngrok 未安装，跳过 Ngrok (pip install pyngrok 可启用)")
        return f"http://localhost:{PORT}"
    try:
        # 清理僵尸进程
        os.system("pkill -f ngrok >/dev/null 2>&1")
        time.sleep(1)

        auth_token = os.environ.get("NGROK_AUTH_TOKEN")
        if auth_token:
            try:
                ngrok.set_auth_token(auth_token)
                logger.info(f"使用Ngrok令牌: {auth_token[:5]}*****")
            except Exception as e:
                logger.error(f"设置Ngrok令牌失败: {e}")
                return f"http://localhost:{PORT}"
        else:
            logger.warning("NGROK_AUTH_TOKEN 未设置，使用本地地址")
            return f"http://localhost:{PORT}"

        logger.info(f"启动 Ngrok 隧道 -> 端口 {PORT} ...")
        tunnel = ngrok.connect(PORT, "http")
        public_url = str(tunnel)
        logger.info(f"Ngrok 隧道启动成功: {public_url} -> http://localhost:{PORT}")
        logger.info(f"配置微信公众号 URL: {public_url}/wechat  Token: (隐藏) 长度={len(PRIMARY_TOKEN)}")
        return public_url
    except Exception as e:
        logger.error(f"Ngrok 隧道启动失败: {e}")
        return f"http://localhost:{PORT}"

if __name__ == '__main__':
    try:
        logger.info(
            "当前主Token长度=%d 兼容Token数量=%d 严格模式=%s", 
            len(PRIMARY_TOKEN), len(EXTRA_TOKENS), STRICT_VERIFY
        )
        if USE_NGROK:
            public_url = start_ngrok()
            if public_url.startswith('http://localhost'):
                logger.warning("使用本地地址，仅供本地测试。若需公网访问请配置 NGROK_AUTH_TOKEN 或使用 FRP/Nginx。")
            else:
                logger.info(f"请在微信公众平台配置: {public_url}/wechat")
        else:
            logger.info("已禁用Ngrok，使用本地地址: http://localhost:%d/wechat", PORT)
            
        # 启动Flask服务
        logger.info(f"微信对接服务启动在端口 {PORT}")
        app.run(host='0.0.0.0', port=PORT)
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
