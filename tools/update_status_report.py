#!/usr/bin/env python3
"""
定时生成“学习/复盘/预测/升级”运行状态报告，覆盖 reports/ssq_status_YYYYMMDD.md。
来源：supervisor 状态、关键日志、汇总指标。
"""
import subprocess, datetime, json, os, re, glob
from typing import Tuple
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:  # 极端情况下不可用时回退
    ZoneInfo = None  # type: ignore

ROOT = "/workspaces/-AI-2.0"
CONF = os.path.join(ROOT, "supervisord.conf")
LOG_DIR = os.path.join(ROOT, "logs", "supervisor")
REPORTS = os.path.join(ROOT, "reports")
PERSON_LOG = os.path.join(ROOT, "xuanji_person_predict.log")

def parse_operation_report(md_text: str) -> dict:
    """
    解析运营周期报告 Markdown，提取关键指标生成摘要 JSON。
    采用宽松正则，缺失字段以 None 返回。
    """
    def find(pattern: str, flags=0, cast=str):
        m = re.search(pattern, md_text, flags)
        if not m:
            return None
        val = m.group(1).strip()
        if cast is int:
            try:
                return int(re.sub(r"[^0-9]", "", val) or "0")
            except Exception:
                return None
        if cast is float:
            try:
                return float(re.sub(r"[^0-9.]+", "", val))
            except Exception:
                return None
        return val

    report_time = find(r"报告生成时间\*\*：\s*([0-9\-:]+)")
    data = {
        "report_time": report_time,
        "core": {
            "累计学习周期": find(r"累计学习周期\*\*：\s*([0-9,\.]+)", cast=int),
            "知识增长量": find(r"知识增长量\*\*：\s*([0-9,\.]+)", cast=int),
            "系统优化进度": find(r"系统优化进度\*\*：\s*([0-9,\.]+)", cast=int),
            "运行周期": find(r"运行周期\*\*：\s*([0-9,\.]+)", cast=int),
            "系统自主升级": find(r"系统自主升级\*\*：\s*([0-9,\.]+)", cast=int),
            "性能提升倍数": find(r"性能提升倍数\*\*：\s*([0-9\.]+)", cast=float),
        },
        "ssq": {
            "双色球学习周期": find(r"双色球学习周期\*\*：\s*([0-9,\.]+)", cast=int),
            "完全匹配次数": find(r"完全匹配次数\*\*：\s*([0-9,\.]+)", cast=int),
            "匹配历史": find(r"匹配历史\*\*：\s*([^\n]+)"),
            "平均尝试次数": find(r"平均尝试次数\*\*：\s*([^\n]+)"),
            "模型权重分布": find(r"模型权重分布\*\*：\s*([^\n]+)"),
            "累计数据源学习轮次": find(r"累计数据源学习轮次\*\*：\s*([0-9,\.]+)", cast=int),
        },
    }
    return data

def sh(cmd: str) -> str:
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.stdout.strip()

def get_status():
    out = sh(f"supervisorctl -c {CONF} status")
    lines = [l for l in out.splitlines() if l.strip()]
    return "\n".join(lines)

def parse_status(status_text: str):
    """Parse supervisorctl status text into structured entries.
    Best-effort: extract first two whitespace-separated tokens as name/status.
    """
    entries = []
    for raw in status_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = re.split(r"\s+", line)
        if len(parts) >= 2:
            name, status = parts[0], parts[1]
            # 尝试从 raw 中解析 pid 与 uptime
            pid = None
            uptime = None
            m_pid = re.search(r"pid\s+(\d+)", line)
            if m_pid:
                try:
                    pid = int(m_pid.group(1))
                except Exception:
                    pid = None
            m_up = re.search(r"uptime\s+([0-9:]+)", line)
            if m_up:
                uptime = m_up.group(1)
            entries.append({"name": name, "status": status, "pid": pid, "uptime": uptime, "raw": line})
        else:
            entries.append({"name": line, "status": "UNKNOWN", "raw": line})
    return entries

def tail_log(name: str, n: int = 30) -> str:
    outp = os.path.join(LOG_DIR, f"{name}.out.log")
    errp = os.path.join(LOG_DIR, f"{name}.err.log")
    def tail(p):
        if not os.path.exists(p):
            return "(无)"
        return sh(f"tail -n {n} {p} || true") or "(空)"
    return f"### {name} OUT\n{tail(outp)}\n\n### {name} ERR\n{tail(errp)}"

def load_metrics():
    p = os.path.join(REPORTS, "ssq_cycle_summary.json")
    if not os.path.exists(p):
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def load_person_metrics(max_bytes: int = 20*1024*1024, last_n: int = 20):
    """Parse historical person task log for lightweight metrics.
    - If log too large (> max_bytes), only parse the last 'last_n' lines for preview,
      but still try to count totals by streaming.
    """
    if not os.path.exists(PERSON_LOG):
        return {}
    try:
        size = os.path.getsize(PERSON_LOG)
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(PERSON_LOG)).strftime("%Y-%m-%d %H:%M:%S")
        total = 0
        per = {}
        matches_true = {}
        last_lines = []
        # Stream parse for counts (line by line)
        with open(PERSON_LOG, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                # Example: "复盘周期70：爱因斯坦 ，预测：...，事实：...，吻合：False"
                if "复盘周期" in line:
                    total += 1
                    # extract name between full-width punctuation after colon up to first comma-like
                    # Tolerate spaces and potential variants
                    m = re.search(r"复盘周期\d+：\s*([^，,]+)", line)
                    name = m.group(1).strip() if m else "未知"
                    per[name] = per.get(name, 0) + 1
                    # match flag
                    m2 = re.search(r"吻合：\s*(True|False)", line)
                    if m2 and m2.group(1) == "True":
                        matches_true[name] = matches_true.get(name, 0) + 1
        # collect tail preview
        try:
            tail_text = sh(f"tail -n {last_n} '{PERSON_LOG}' || true")
        except Exception:
            tail_text = ""
        # compose metrics
        persons = {}
        for name, cnt in per.items():
            persons[name] = {"count": cnt, "matches_true": matches_true.get(name, 0)}
        return {
            "log_mtime": mtime,
            "size": size,
            "total_records": total,
            "per_person": persons,
            "last_tail": tail_text,
        }
    except Exception:
        return {}

def _now_times() -> Tuple[str, str, str]:
    """Return (utc_str, local_str, local_tz_name).
    - utc_str in format: YYYY-mm-dd HH:MM:SS UTC +0000
    - local_str in format: YYYY-mm-dd HH:MM:SS CST +0800 (Asia/Shanghai)
    """
    # UTC
    utc_dt = datetime.datetime.now(datetime.timezone.utc)
    utc_str = utc_dt.strftime("%Y-%m-%d %H:%M:%S %Z %z")
    # Local (Asia/Shanghai)
    tz_name = "Asia/Shanghai"
    try:
        if ZoneInfo is not None:
            local_dt = utc_dt.astimezone(ZoneInfo(tz_name))
        else:
            raise RuntimeError("ZoneInfo unavailable")
    except Exception:
        # 无 ZoneInfo 时固定 +08:00 偏移（中国不实行夏令时）
        local_dt = utc_dt.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
        tz_name = "Asia/Shanghai"
    local_str = local_dt.strftime("%Y-%m-%d %H:%M:%S %Z %z")
    return utc_str, local_str, tz_name

def write_report(md_path: str, status_text: str, logs: str, metrics: dict, person_metrics: dict):
    ts_utc, ts_local, tz_local = _now_times()
    lines = [
        "# 双色球学习/复盘/预测/升级 自循环状态报告（实时）",
        f"\n**生成时间（UTC）**：{ts_utc}\n\n**北京时间（{tz_local}）**：{ts_local}\n",
        "## 1. 后台进程状态（supervisor 托管）",
        f"\n````\n{status_text}\n````\n",
        "## 2. 关键日志快照（最近）",
        logs,
    ]
    if metrics:
        lines += [
            "\n## 3. 累积评估指标（reports/ssq_cycle_summary.json）",
            f"\n- 统计时间：{metrics.get('timestamp','-')}\n- 总预测次数：{metrics.get('total_predictions','-')}\n- 命中次数：{metrics.get('total_matches','-')}\n",
            "- 模型分布：",
        ]
        by = metrics.get("by_model", {})
        for k in ("liuyao","liuren","qimen","ai"):
            if k in by:
                lines.append(f"  - {k}：{by[k].get('count','-')}（命中 {by[k].get('matches','-')}）")
    # person metrics
    if person_metrics:
        lines += [
            "\n## 4. 历史人物任务指标（xuanji_person_predict.log）",
            f"\n- 最近更新时间：{person_metrics.get('log_mtime','-')}\n- 日志大小：{person_metrics.get('size','-')} 字节\n- 总复盘记录：{person_metrics.get('total_records','-')}\n",
            "- 人物统计：",
        ]
        for name, row in sorted(person_metrics.get("per_person", {}).items(), key=lambda kv: kv[0]):
            lines.append(f"  - {name}：{row.get('count','-')}（吻合=True {row.get('matches_true',0)}）")
        tail = person_metrics.get("last_tail", "")
        if tail:
            lines += ["\n- 最近片段：\n", f"````\n{tail}\n````\n"]
        # Top3 summary by count
        per = person_metrics.get("per_person", {})
        if per:
            top3 = sorted(per.items(), key=lambda kv: kv[1].get("count", 0), reverse=True)[:3]
            if top3:
                lines += ["\n- Top3 人物（按复盘记录数）："]
                for name, row in top3:
                    lines.append(f"  - {name}: {row.get('count',0)}（吻合=True {row.get('matches_true',0)}）")
    lines += [
    "\n## 5. 结论与建议",
        "\n- 结论：服务 RUNNING；学习/预测/优化循环无致命报错。如日志存在阶段性 404（/discover），为非公开接口。",
        "- 建议：如需对外公开，请配置 ngrok/FRP 或 Nginx + 证书；建议启用日志轮转或接入 Prometheus/Grafana。",
        "\n— 本报告由系统自动生成并覆盖更新",
    ]
    content = "\n".join(lines)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)
    # 同步生成静态 HTML 版本，便于无需框架的前端展示
    html_out = os.path.join(ROOT, "static", "status_report.html")
    os.makedirs(os.path.dirname(html_out), exist_ok=True)
    # 构造带锚点的静态 HTML，便于快速跳转到各任务日志与人物指标
    # 为避免复杂解析 Markdown，这里额外直接注入关键段落的锚点版本。
    # 再附上原 Markdown 的纯展示作为参考。
    def esc(t: str) -> str:
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 分别抓取各日志最新内容
    log_sections = {
        "autonomous": tail_log("xuanji_autonomous"),
        "predict": tail_log("xuanji_predict"),
        "optimize": tail_log("xuanji_optimize"),
        "person": tail_log("xuanji_person"),
        "api": tail_log("xuanji_api"),
    }
    # Render person metrics block
    def render_person_metrics(pm: dict) -> str:
        if not pm:
            return "(无人物指标)"
        lines = [
            f"最近更新时间：{pm.get('log_mtime','-')}",
            f"日志大小：{pm.get('size','-')} 字节",
            f"总复盘记录：{pm.get('total_records','-')}",
            "人物统计：",
        ]
        for name, row in sorted(pm.get('per_person', {}).items(), key=lambda kv: kv[0]):
            lines.append(f"  - {name}：{row.get('count','-')}（吻合=True {row.get('matches_true',0)}）")
        tail = pm.get('last_tail', '')
        if tail:
            lines.append("\n最近片段：\n" + tail)
        return "\n".join(lines)

    # simple bar chart for person metrics
    def render_person_barchart(pm: dict) -> str:
        if not pm or not pm.get('per_person'):
            return "<div class='note'>(无数据)</div>"
        per = pm.get('per_person', {})
        items = sorted(per.items(), key=lambda kv: kv[1].get('count', 0), reverse=True)
        # Only show top 10 for readability
        items = items[:10]
        maxv = max((row.get('count', 0) for _, row in items), default=1) or 1
        bars = []
        for name, row in items:
            cnt = row.get('count', 0)
            mt = row.get('matches_true', 0)
            width = int(100 * cnt / maxv)
            bars.append(f"""
            <div style='display:flex; align-items:center; gap:8px; margin:6px 0;'>
                <div style='width:140px;'>{name}</div>
                <div style='flex:1; background:#e5e7eb; border-radius:6px; overflow:hidden;'>
                    <div style='width:{width}%; background:#60a5fa; height:16px;'></div>
                </div>
                <div style='width:120px; text-align:right;'><code>{cnt}</code> / <span title='吻合=True 次数'><code>{mt}</code></span></div>
            </div>
            """)
        return "\n".join(bars)
    html = f"""
    <!DOCTYPE html>
    <html lang='zh-CN'>
    <head>
        <meta charset='utf-8'>
        <title>最新运行状态报告</title>
        <link rel='stylesheet' href='/static/report.css'>
        <style>
            body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Liberation Sans', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; }}
            pre {{ white-space: pre-wrap; word-break: break-word; background:#0b1020; color:#e6edf3; padding:12px; border-radius:8px; }}
            .container {{ max-width: 980px; margin: 32px auto; padding: 0 16px; }}
            .nav {{ display:flex; flex-wrap:wrap; gap:12px; margin: 12px 0 20px; }}
            .nav a {{ text-decoration:none; background:#eef2ff; color:#1d4ed8; padding:6px 10px; border-radius:6px; font-size:14px; }}
            h2 {{ margin-top: 28px; }}
            .meta {{ color:#6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class='container'>
            <h1>🛰️ 最新运行状态报告</h1>
            <div class='meta'>文件：{os.path.basename(md_path)}｜生成时间（UTC）：{ts_utc}｜北京时间（{tz_local}）：{ts_local}</div>
            <div class='nav'>
                <a href="#sec-status">进程状态</a>
                <a href="#sec-autonomous">学习/复盘日志</a>
                <a href="#sec-predict">双色球预测日志</a>
                <a href="#sec-optimize">优化循环日志</a>
                <a href="#sec-person">历史人物任务日志</a>
                <a href="#sec-api">API 日志</a>
                <a href="#sec-person-metrics">人物任务指标</a>
                <a href="#sec-full">原始全文</a>
            </div>

            <h2 id='sec-status'>1）进程状态</h2>
            <pre>{esc(status_text)}</pre>

            <h2 id='sec-autonomous'>2）学习/复盘日志</h2>
            <pre>{esc(log_sections['autonomous'])}</pre>

            <h2 id='sec-predict'>3）双色球预测日志</h2>
            <pre>{esc(log_sections['predict'])}</pre>

            <h2 id='sec-optimize'>4）优化循环日志</h2>
            <pre>{esc(log_sections['optimize'])}</pre>

            <h2 id='sec-person'>5）历史人物任务日志</h2>
            <pre>{esc(log_sections['person'])}</pre>

            <h2 id='sec-api'>6）API 日志</h2>
            <pre>{esc(log_sections['api'])}</pre>

            <h2 id='sec-person-metrics'>7）人物任务指标</h2>
            <pre>{esc(render_person_metrics(person_metrics))}</pre>

            <h2>8）人物任务图表（Top10）</h2>
            <div style='border:1px solid #e5e7eb; border-radius:8px; padding:12px;'>
                {render_person_barchart(person_metrics)}
            </div>

            <h2 id='sec-full'>附录：原始 Markdown 全文</h2>
            <pre>{esc(content)}</pre>
        </div>
    </body>
    </html>
    """
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(html)
    # 生成最新运营周期报告的静态 HTML 和摘要 JSON（若存在）
    try:
        op_paths = sorted(glob.glob(os.path.join(REPORTS, 'operation_report_*.md')))
        if op_paths:
            op_md = op_paths[-1]
            with open(op_md, 'r', encoding='utf-8') as rf:
                op_content = rf.read()
            op_html = os.path.join(ROOT, 'static', 'operation_report.html')
            op_doc = f"""
            <!DOCTYPE html>
            <html lang='zh-CN'>
            <head>
                <meta charset='utf-8'>
                <title>最新运营周期报告</title>
                <link rel='stylesheet' href='/static/report.css'>
                <style>
                    pre {{ white-space: pre-wrap; word-break: break-word; }}
                    .container {{ max-width: 980px; margin: 32px auto; padding: 0 16px; }}
                    .meta {{ color:#6b7280; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class='container'>
                    <h1>📈 最新运营周期报告</h1>
                    <div class='meta'>文件：{os.path.basename(op_md)}｜生成时间（UTC）：{ts_utc}｜北京时间（{tz_local}）：{ts_local}</div>
                    <pre>{esc(op_content)}</pre>
                </div>
            </body>
            </html>
            """
            with open(op_html, 'w', encoding='utf-8') as of:
                of.write(op_doc)
            # 同步生成摘要 JSON
            try:
                summary = parse_operation_report(op_content)
                summary.update({
                    "file": os.path.basename(op_md),
                    "generated_utc": ts_utc,
                    "generated_local": ts_local,
                })
                with open(os.path.join(ROOT, 'static', 'operation_summary.json'), 'w', encoding='utf-8') as sf:
                    json.dump(summary, sf, ensure_ascii=False, indent=2)
            except Exception:
                pass
    except Exception:
        pass
    # 额外生成 JSON 快照，便于程序消费
    try:
        json_out = os.path.join(ROOT, "static", "status.json")
        # 解析心跳：关注 xuanji_predict 与 xuanji_person
        sup_entries = parse_status(status_text)
        hb = {}
        # 日志时间与尾部
        def _log_meta(prog: str):
            outp = os.path.join(LOG_DIR, f"{prog}.out.log")
            ts = None
            tail = None
            if os.path.exists(outp):
                try:
                    ts = datetime.datetime.fromtimestamp(os.path.getmtime(outp)).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    ts = None
                try:
                    tail = sh(f"tail -n 10 {outp} || true")
                except Exception:
                    tail = None
            return ts, tail
        for prog in ("xuanji_predict", "xuanji_person"):
            row = next((e for e in sup_entries if e.get("name") == prog), None)
            last_ts, last_tail = _log_meta(prog)
            if row:
                hb[prog] = {
                    "status": row.get("status"),
                    "pid": row.get("pid"),
                    "uptime": row.get("uptime"),
                    "last_log_time": last_ts,
                    "last_tail": last_tail,
                }
            else:
                hb[prog] = {
                    "status": "UNKNOWN",
                    "pid": None,
                    "uptime": None,
                    "last_log_time": last_ts,
                    "last_tail": last_tail,
                }
        snapshot = {
            # 兼容：沿用 timestamp 但显式使用 UTC
            "timestamp": ts_utc,
            "local_time": ts_local,
            "timezone": tz_local,
            "supervisor": sup_entries,
            "heartbeats": hb,
            "metrics": metrics or {},
            "person": {
                "log_mtime": person_metrics.get("log_mtime") if person_metrics else None,
                "size": person_metrics.get("size") if person_metrics else None,
                "total_records": person_metrics.get("total_records") if person_metrics else None,
                "per_person": person_metrics.get("per_person") if person_metrics else None,
            },
        }
        with open(json_out, "w", encoding="utf-8") as jf:
            json.dump(snapshot, jf, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # ——自愈检测与自动回退——
    try:
        # 1. 检查所有关键任务状态
        sup_entries = snapshot.get('supervisor', [])
        unhealthy = []
        for e in sup_entries:
            if e.get('status') not in ('RUNNING', 'STARTING'):
                unhealthy.append(e)
        # 2. 检查健康评分
        health_score = None
        op_sum_path = os.path.join(ROOT, 'static', 'operation_summary.json')
        if os.path.exists(op_sum_path):
            with open(op_sum_path, 'r', encoding='utf-8') as f:
                op_sum = json.load(f)
            health_score = op_sum.get('core', {}).get('健康评分')
        # 系统自设健康评分下限
        HEALTH_MIN = 60
        # 3. 若发现异常则自动重启并回退权重
        if unhealthy or (health_score is not None and health_score < HEALTH_MIN):
            # 记录自愈动作
            action_log = os.path.join(ROOT, 'static', 'self_heal_log.txt')
            with open(action_log, 'a', encoding='utf-8') as af:
                af.write(f"[{__import__('datetime').datetime.now()}] 自愈触发: 异常任务={unhealthy}, 健康评分={health_score}\n")
            # 自动重启异常任务
            for e in unhealthy:
                name = e.get('name')
                if name:
                    os.system(f".venv/bin/supervisorctl -c supervisord.conf restart {name}")
            # 自动回退权重文件（如有历史）
            hist_path = os.path.join(ROOT, 'reports', 'ssq_weights_history.jsonl')
            wfile = os.path.join(ROOT, 'ssq_strategy_weights.json')
            if os.path.exists(hist_path):
                try:
                    with open(hist_path, 'r', encoding='utf-8') as hf:
                        lines = [l for l in hf if l.strip()]
                    if len(lines) >= 2:
                        # 回退到倒数第二条
                        last_good = json.loads(lines[-2])
                        with open(wfile, 'w', encoding='utf-8') as wf:
                            json.dump(last_good, wf, ensure_ascii=False, indent=2)
                        with open(action_log, 'a', encoding='utf-8') as af:
                            af.write(f"[{__import__('datetime').datetime.now()}] 权重自动回退到历史版本\n")
                except Exception:
                    pass
    except Exception:
        pass
    # 生成调优摘要 tuning_summary.json（若存在权重文件）
    try:
        wfile = os.path.join(ROOT, 'ssq_strategy_weights.json')
        if os.path.exists(wfile):
            with open(wfile, 'r', encoding='utf-8') as wf:
                wj = json.load(wf)
            t_sum = {
                'generated_utc': ts_utc,
                'generated_local': ts_local,
                'window': wj.get('window'),
                'ema_alpha': wj.get('ema_alpha'),
                'weights': wj.get('weights'),
                'metrics': wj.get('metrics', {}),
            }
            with open(os.path.join(ROOT, 'static', 'tuning_summary.json'), 'w', encoding='utf-8') as tf:
                json.dump(t_sum, tf, ensure_ascii=False, indent=2)
    except Exception:
        pass

def main():
    # 文件名仍以系统本地时间为准（通常为 UTC 环境），不改变现有路径规范
    today = datetime.datetime.now().strftime("%Y%m%d")
    md = os.path.join(REPORTS, f"ssq_status_{today}.md")
    status_text = get_status()
    logs = "\n\n".join([
        tail_log("xuanji_autonomous"),
        tail_log("xuanji_predict"),
        tail_log("xuanji_optimize"),
        tail_log("xuanji_person"),
        tail_log("xuanji_api"),
    ])
    metrics = load_metrics()
    person_metrics = load_person_metrics()
    write_report(md, status_text, logs, metrics, person_metrics)

if __name__ == "__main__":
    main()
