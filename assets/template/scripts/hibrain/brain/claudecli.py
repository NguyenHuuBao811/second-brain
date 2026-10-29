"""Chạy claude: env gateway, quota, sandbox, eval."""
import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
import brain_kb
from . import config, learnrun, util

def brain_env():
    """Môi trường cho mọi lần brain gọi Claude: đánh dấu phiên để collect bỏ qua."""
    return {**os.environ, "CLAUDE_CODE_ENTRYPOINT": config.BRAIN_ENTRYPOINT}

# Claude: chạy bằng tài khoản Claude trước, hết quota thì chạy lại qua gateway (vd 9router).
AUTH_KEYS = ("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY", "ANTHROPIC_DEFAULT_OPUS_MODEL",
             "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL")
QUOTA_RE = re.compile(r'"api_error"\s*:\s*"usage_limit_reached"|"is_error"\s*:\s*true.*"result"\s*:\s*"[^"]*'
                      r'(?:hit your [a-z ]*limit|usage limit reached)', re.I | re.S)
QUOTA_COOLDOWN = 3600
USER_SETTINGS = Path.home() / ".claude" / "settings.json"

def gateway_env():
    """Env của gateway dự phòng: HIBRAIN_GATEWAY_<KEY> (private/claude.env), không có thì lấy `env` trong
    ~/.claude/settings.json. Không có BASE_URL hoặc HIBRAIN_GATEWAY=0 thì không có gateway."""
    util.load_env()
    if os.environ.get("HIBRAIN_GATEWAY") == "0":
        return {}
    gw = {k: os.environ[f"HIBRAIN_GATEWAY_{k}"] for k in AUTH_KEYS if os.environ.get(f"HIBRAIN_GATEWAY_{k}")}
    if not gw:
        try:
            user = json.loads(USER_SETTINGS.read_text(encoding="utf-8")).get("env") or {}
        except (OSError, ValueError, AttributeError):
            user = {}
        gw = {k: str(user[k]) for k in AUTH_KEYS if user.get(k)}
    return gw if gw.get("ANTHROPIC_BASE_URL") else {}

def _with_settings(cmd, env_override):
    """Gộp mọi --settings thành một (CLI chỉ nhận cái cuối), thêm env_override vào `env` của nó.
    `env` trong --settings đè cả ~/.claude/settings.json lẫn env tiến trình."""
    out, merged, i = [], {}, 0
    while i < len(cmd):
        if cmd[i] == "--settings" and i + 1 < len(cmd):
            v = str(cmd[i + 1])
            try:
                d = json.loads(v if v.lstrip().startswith("{") else Path(v).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                d = {}
            merged = {**merged, **d, "env": {**(merged.get("env") or {}), **(d.get("env") or {})}}
            i += 2
            continue
        out.append(cmd[i])
        i += 1
    merged["env"] = {**merged.get("env", {}), **env_override}
    if not merged["env"]:
        del merged["env"]
    return out + (["--settings", json.dumps(merged)] if merged else [])

def _quota_file():
    return config.LOGS / "claude-quota.txt"

def _quota_cooling():
    try:
        return time.time() - float(_quota_file().read_text()) < QUOTA_COOLDOWN
    except (OSError, ValueError):
        return False

def run_claude(cmd, **kw):
    """subprocess.run cho claude CLI (cần capture_output + text). Có gateway thì lượt đầu ép dùng tài khoản Claude,
    hết quota thì chạy lại qua gateway; trong QUOTA_COOLDOWN giây sau đó đi thẳng gateway. Không có gateway: như cũ."""
    env = dict(kw.pop("env", None) or os.environ)
    gw = gateway_env()
    if not gw:
        return subprocess.run(cmd, env=env, **kw)
    if not _quota_cooling():
        own = {k: v for k, v in env.items() if k not in AUTH_KEYS}   # settings env "" đè ~/.claude/settings.json
        r = subprocess.run(_with_settings(cmd, dict.fromkeys(AUTH_KEYS, "")), env=own, **kw)
        if not QUOTA_RE.search(r.stdout or ""):
            return r
        config.LOGS.mkdir(exist_ok=True)
        _quota_file().write_text(str(time.time()))
        util.log(f"claude: tài khoản hết quota, chuyển sang gateway {gw['ANTHROPIC_BASE_URL'].split('//')[-1].split('/')[0]}")
    return subprocess.run(_with_settings(cmd, {}), env={**env, **gw}, **kw)


EVAL_PROMPT = """BRAIN_ROLE: eval
Trả lời câu hỏi CHỈ dựa vào second brain trong thư mục hiện tại (đọc INDEX.md, chỉ mục con indexes/, rồi file liên quan).
Không đọc raw/, 00-inbox/, eval/, logs/, private/. Không có trong brain thì answer là "không có trong brain".
Câu hỏi: {q}
Trả về DUY NHẤT một JSON: {{"answer": "<ngắn>", "cited_pages": ["<đường dẫn file đã dùng>"]}}"""


def cmd_eval(n=None, model="sonnet", budget=2.0, dry=False, sets=("golden", "golden-lark")):
    """Chạy bộ câu hỏi vàng: mỗi câu ghi hit/đúng/trả lời được/thời gian/token vào logs/eval-<ngày>.jsonl và
    eval/results-auto-<ngày>.md. --dry: chỉ liệt kê câu, không gọi model. Dừng khi chạm trần `budget` USD."""
    util.load_env()
    rows = brain_kb.load_golden(config.BASE, sets)[:n or None]
    if dry:
        for r in rows:
            print(f"- [{r['set']}/{r.get('kind', '-')}] {r['q']} → {', '.join(r.get('expected_pages') or []) or '(bẫy)'}")
        print(f"(dry) {len(rows)} câu, không gọi model")
        return 0
    out, cost = [], 0.0
    for r in rows:
        if budget - cost <= 0.01:
            util.log(f"eval: chạm trần {budget} USD sau {len(out)} câu")
            break
        t0 = time.time()
        d = _claude_run(EVAL_PROMPT.format(q=r["q"]), model, "Read,Grep,Glob", config.BASE,
                        max_budget=round(min(budget - cost, 0.5), 2), timeout=600)
        cost += d.get("total_cost_usd") or 0
        ans = learnrun.parse_json(str(d.get("result") or "")) or {}
        rec = {**r, **brain_kb.score_eval(r, str(ans.get("answer") or ""), ans.get("cited_pages") or []),
               "cited": [str(c) for c in ans.get("cited_pages") or []][:10], "duration_s": round(time.time() - t0, 2),
               "tokens": _usage_total(d), "cost": d.get("total_cost_usd") or 0, "ok": not d.get("is_error")}
        out.append(rec)
    day = f"{datetime.now():%Y-%m-%d}"
    config.LOGS.mkdir(exist_ok=True)
    with open(config.LOGS / f"eval-{day}.jsonl", "a", encoding="utf-8") as f:
        f.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in out)
    rep = brain_kb.eval_report(out, model)
    (config.BASE / "eval" / f"results-auto-{day}.md").write_text(rep, encoding="utf-8")
    print(rep)
    print(f"est_usd={cost:.2f}")
    return 0


def _usage_total(d):
    u = (d or {}).get("usage") or {}
    return sum(int(u.get(k) or 0) for k in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                                            "cache_creation_input_tokens")) or None


def _claude_run(prompt, model, tools, cwd, settings=None, timeout=900, max_budget=None, extra_args=None):
    """claude -p ... --output-format json, trả dict kết quả (có usage nếu CLI có). Lỗi: {"is_error": True, ...}."""
    claude = util.find_claude()
    if not claude:
        return {"is_error": True, "result": "claude CLI not found", "total_cost_usd": 0}
    cmd = [sys.executable, claude] if claude.endswith(".py") else [claude]
    cmd += ["-p", "--model", model, "--output-format", "json", "--max-turns", "15"]
    cmd += ["--tools", tools] if tools is not None else []
    if tools:
        cmd += ["--allowedTools", tools]
    if settings:
        cmd += ["--settings", str(settings)]
    if max_budget is not None:
        cmd += ["--max-budget-usd", str(max_budget)]
    if extra_args:
        cmd += list(extra_args)
    try:
        r = run_claude(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
                       cwd=cwd, timeout=timeout, env=brain_env())
    except subprocess.TimeoutExpired:
        return {"is_error": True, "result": "timeout", "total_cost_usd": max_budget or 0.5}
    try:
        d = json.loads(r.stdout)
        return d if isinstance(d, dict) else {"is_error": True, "result": str(d)[:500], "total_cost_usd": 0}
    except Exception:
        return {"is_error": True, "result": (r.stdout + r.stderr)[:500], "total_cost_usd": 0, "_raw": True}


def _claude_text(prompt, model, tools, cwd, settings=None, timeout=900, max_budget=None, extra_args=None):
    claude = util.find_claude()
    if not claude:
        return "claude CLI not found", 0, False
    cmd = [sys.executable, claude] if claude.endswith(".py") else [claude]
    cmd += ["-p", "--model", model, "--output-format", "json", "--max-turns", "15"]
    cmd += ["--tools", tools] if tools is not None else []
    if tools:
        cmd += ["--allowedTools", tools]
    if settings:
        cmd += ["--settings", str(settings)]
    if max_budget is not None:
        cmd += ["--max-budget-usd", str(max_budget)]
    if extra_args:
        cmd += list(extra_args)
    try:
        r = run_claude(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
                           cwd=cwd, timeout=timeout, env=brain_env())
    except subprocess.TimeoutExpired:
        return "timeout", max_budget or 0.5, False
    try:
        d = json.loads(r.stdout)
        return (d.get("result") or "").strip(), d.get("total_cost_usd", 0), not d.get("is_error")
    except Exception:
        return (r.stdout + r.stderr)[:500], 0, False


def _sandbox_settings_json(blocked_paths):
    """JSON settings chặn đọc các đường dẫn trong blocked_paths (brain thật, thư mục chat...)."""
    deny = [f"{tool}(/{p.as_posix()}/**)" for p in blocked_paths for tool in ("Read", "Grep", "Glob")]
    return json.dumps({"permissions": {"deny": deny}}, indent=2)


@contextlib.contextmanager
def _make_sandbox(overlay=None, prefix="brain-sim-", root=None):
    """Bản sao brain chỉ chứa phần đã tinh luyện, dùng cho persona-eval/agora. Dọn dẹp kể cả khi lỗi.

    root: brain nguồn để sao chép (mặc định BASE). Agora dùng AGORA_ROOT, có thể khác BASE.
    overlay: text thêm vào cuối 50-knowledge/owner-model.md trong bản sao (tạo file nếu chưa có).
    """
    root = root or config.BASE
    sandbox = Path(tempfile.mkdtemp(prefix=prefix))
    settings = sandbox.parent / f"{sandbox.name}-settings.json"
    try:
        for item in ["AGENTS.md", "CLAUDE.md", "CRITICAL.md", "INDEX.md", "10-daily", "20-projects", "25-areas", "30-people",
                     "40-decisions", "50-knowledge", "90-reference"]:
            src = root / item
            if src.is_dir():
                shutil.copytree(src, sandbox / item)
            elif src.exists():
                shutil.copy2(src, sandbox / item)
        if overlay:
            owner = sandbox / "50-knowledge" / "owner-model.md"
            owner.parent.mkdir(parents=True, exist_ok=True)
            prev = owner.read_text(encoding="utf-8") if owner.exists() else ""
            sep = "\n" if prev and not prev.endswith("\n") else ""
            owner.write_text(prev + sep + overlay, encoding="utf-8")
        # Bản sao chưa đủ: Read vẫn mở được file thật bằng đường dẫn tuyệt đối.
        # Chặn toàn bộ brain gốc (BASE và root nếu khác) và thư mục chat của Claude Code.
        # Dùng "//" = đường dẫn tuyệt đối, kèm cả dạng đã resolve (macOS: /tmp -> /private/tmp) lẫn dạng gốc.
        blocked = {config.BASE, config.BASE.resolve(), root, root.resolve(), Path.home() / ".claude" / "projects"}
        settings.write_text(_sandbox_settings_json(blocked), encoding="utf-8")
        yield sandbox, settings
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
        settings.unlink(missing_ok=True)
