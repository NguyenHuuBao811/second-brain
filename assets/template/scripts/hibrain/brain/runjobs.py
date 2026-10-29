"""Chạy job headless (ingest, reflect, lint...), inbox theo máy, vai trò (roles)."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime
import brain_kb
from . import claudecli, config, factcheck, larkcli, learnrun, setup, textsafe, util

# ---------------------------------------------------------------- commands
def recent_run_by_other(job):
    """Máy khác đã chạy job này trong kỳ hiện tại chưa (đọc từ commit message `job ... [host]`)."""
    since = config.SHARED_JOBS.get(job)
    if not since:
        return None
    subjects = util.git("log", f"--since={since}", "--format=%s", f"--grep=^{job} ").stdout.splitlines()
    hosts = [m.group(1) for m in (re.search(r"\[([^\]]+)\]$", s) for s in subjects) if m]
    return next((h for h in hosts if h != config.HOST), None)

INBOX_HANDOVER_SECONDS = 3 * 3600

def inbox_owner(path):
    """Máy đã đưa file inbox này vào git, và lúc nào. Chưa commit thì là file của máy này."""
    rel = path.relative_to(config.BASE).as_posix()
    out = util.git("log", "--diff-filter=A", "-1", "--format=%ct %s", "--", rel).stdout.strip()
    if not out:
        return config.HOST, time.time()
    ts, _, subject = out.partition(" ")
    m = re.search(r"\[([^\]]+)\]$", subject) or re.search(r"^inbox from (\S+)", subject)
    return (m.group(1) if m else None), int(ts)

def my_inbox_files():
    """Inbox dùng chung: máy đẩy file lên thì máy đó nạp, để hai máy không nạp trùng.
    Quá INBOX_HANDOVER_SECONDS mà chưa ai nạp (máy kia tắt) thì máy nào cũng nhận."""
    mine = []
    for p in sorted(config.INBOX.glob("*.md")):
        owner, ts = inbox_owner(p)
        if owner in (None, config.HOST) or time.time() - ts > INBOX_HANDOVER_SECONDS:
            mine.append(p)
    return mine + sorted(config.LOCAL_INBOX.glob("*.md")) + sorted(larkcli.LARK_INBOX.glob("*.md")) + setup.lark_feedback_ready()

# Mỗi lần ingest tối đa N file: một lần chạy có trần 3 USD / 40 lượt; hàng đợi lớn (vd lần đầu kéo nhiều nhóm Lark)
# mà nạp hết một lượt thì chạy không xong, file không được dời đi, giờ sau chạy lại y như cũ và tốn tiền mãi.
INGEST_BATCH = 5

def ingest_batch(n=None):
    return my_inbox_files()[:n or INGEST_BATCH]

def run_limits(n):
    """(max-turns, max-budget-usd) cho một lần ingest n file: mặc định 40 lượt / 3 USD, lớn hơn thì theo số file."""
    return max(40, 3 * n), max(3, round(n * 0.25))

def cmd_run(job, model, sync=True, force=False, batch=None, dry=False):
    if job == "learn":
        return learnrun.cmd_learn(model, sync, force, dry)
    with util.Lock(job) as lock:
        if lock is None:
            util.log(f"{job} skipped: already running")
            return 0
        util.load_env()
        if sync:
            util.pull()
        other = None if force else recent_run_by_other(job)
        if other:
            util.log(f"{job} skipped: {other} đã chạy kỳ này (dùng --force để chạy lại)")
            return 0
        inbox = ingest_batch(batch) if job == "ingest" else []
        turns, budget = run_limits(len(inbox) if batch else INGEST_BATCH)
        if job == "ingest" and not inbox:
            if sync:
                util.push()
            return 0
        if job == "lint":
            lint_precheck()
        claude = util.find_claude()
        if not claude:
            util.log("ERROR claude CLI not found. Cài Claude Code hoặc thêm vào PATH.")
            return 1
        if os.environ.get("CLAUDE_BIN"):
            util.log(f"using CLAUDE_BIN={claude}")

        # Khoá chung với mọi job khác ghi vào brain (vd apply-lesson của agora),
        # tránh hai tiến trình commit chồng lên nhau.
        with util.Lock("brain-write") as wlock:
            if wlock is None:
                util.log(f"{job} skipped: brain-write busy")
                return 0
            tools = ["Read", "Grep", "Glob"]
            tools += [f"{op}({d}/**)" for d in config.DATA_DIRS for op in ("Edit", "Write")]
            tools += [f"Edit({f})" for f in config.DATA_FILES]
            if job == "ingest":
                # Inbox dùng chung nhiều máy: chỉ nạp file của máy này (xem my_inbox_files).
                queue = config.LOGS / "ingest-queue.txt"
                queue.write_text("".join(f"{q.relative_to(config.BASE).as_posix()}\n" for q in inbox), encoding="utf-8")
            ok = True
            for stage, prompt_file, stage_model in role_stages(job, model):
                # Prompt ngắn, không ký tự đặc biệt: tránh lỗi escape trên Windows cmd.
                prompt = (f"Read the file prompts/{prompt_file}.md and follow its instructions exactly. "
                          f"Today is {datetime.now():%Y-%m-%d}.")
                if job == "lint" and (config.LOGS / CHECK_LATEST).exists():
                    prompt += f" First read logs/{CHECK_LATEST}: deterministic check output, include it in the report."
                if job == "ingest":
                    prompt += " Only process the inbox files listed in logs/ingest-queue.txt."
                ok = _job_agent(claude, f"{job}:{stage}" if stage else job, prompt, stage_model, turns, budget, tools)
                if not ok:
                    break
            if job == "ingest" and ok and roles_on():
                roles_verify(inbox)

            if job == "ingest" and ok:
                factcheck.archive_ingested(inbox)
                for p in inbox:
                    if p.exists():
                        done = p.parent / "done"
                        done.mkdir(exist_ok=True)
                        target = done / p.name
                        if target.exists():
                            target = done / f"{p.stem}-{datetime.now():%Y%m%d%H%M}{p.suffix}"
                        shutil.move(str(p), str(target))

            ctrl = util.git("status", "--porcelain", "--", *config.CONTROL).stdout.strip()
            if ctrl:
                util.log(f"WARN control files changed locally, not committed: {ctrl.replace(chr(10), ', ')}")
            util.commit(f"{job} {datetime.now():%Y-%m-%d-%H%M} [{config.HOST}]",
                   ["00-inbox", *config.DATA_DIRS, *config.DATA_FILES])
        if sync:
            util.push()
        return 0 if ok else 1


def _job_agent(claude, label, prompt, model, turns, budget, tools):
    """Một lượt agent headless của job (không Bash/Web/MCP, chỉ ghi thư mục dữ liệu). Trả ok."""
    out = config.LOGS / f"{label.replace(':', '-')}-{datetime.now():%Y-%m-%d-%H%M}.json"
    cmd = [claude, "-p", prompt, "--model", model, "--max-turns", str(turns),
           "--max-budget-usd", str(budget), "--settings", str(config.BASE / "headless" / "settings.json"),
           "--tools", "Read,Grep,Glob,Edit,Write",  # không có Bash, WebFetch, MCP
           "--allowedTools", ",".join(tools), "--output-format", "json"]
    stderr = ""
    try:
        r = claudecli.run_claude(cmd, cwd=config.BASE, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       stdin=subprocess.DEVNULL, timeout=1800, env=claudecli.brain_env())
        stderr = r.stderr or ""
        out.write_text(textsafe.redact(r.stdout + r.stderr), encoding="utf-8")
        rc = r.returncode
    except subprocess.TimeoutExpired:
        rc, stderr = 124, "quá 1800 giây, đã dừng"
    try:
        # CLI có thể in cảnh báo (vd "connectors are disabled") trước JSON: bỏ phần đó.
        raw = out.read_text(encoding="utf-8")
        res = json.loads(raw[raw.index("{"):])
    except Exception:
        res = {"is_error": True, "result": out.read_text(encoding="utf-8", errors="replace")[:300]
               if out.exists() else ""}
    ok = rc == 0 and not res.get("is_error")
    util.log(f"{label} rc={rc} ok={ok} est_usd={res.get('total_cost_usd', 0):.2f}"
        + ("" if ok else f" error={str(res.get('result'))[:200]}"))
    if not ok:
        factcheck.log_job_error(label, rc, res, stderr)
    return ok


# Tách vai agent (P17 giai đoạn 4). Mặc định một agent như cũ; BRAIN_ROLES=1 thì ingest chạy trích → thủ thư,
# rồi kiểm (verify-sample trên file vừa đổi). Vai trả lời: prompts/role-answer.md, bot Lark nạp khi BRAIN_ROLES=1.
ROLE_PROMPTS = {"extract": "role-extract", "verify": "role-verify", "librarian": "role-librarian",
                "answer": "role-answer"}


def roles_on():
    return os.environ.get("BRAIN_ROLES", "0") == "1"


def role_model(role, default):
    return os.environ.get(f"BRAIN_MODEL_{role.upper()}") or default


def role_stages(job, model):
    """[(tên vai | None, file prompt, model)] cho một job."""
    if job != "ingest" or not roles_on():
        return [(None, job, model)]
    return [("extract", ROLE_PROMPTS["extract"], role_model("extract", "haiku")),
            ("librarian", ROLE_PROMPTS["librarian"], role_model("librarian", model))]


def roles_verify(inbox, n=None, budget=None):
    """Vai kiểm: đối chiếu fact vừa ghi (file đổi trong lượt này) với bản gốc trong inbox. Sai thì vào review-queue."""
    changed = {l[3:].strip() for l in util.git("status", "--porcelain", "-uall", "--", *config.DATA_DIRS).stdout.splitlines()}
    facts = [f for f in brain_kb.fact_lines(config.BASE) if f["path"] in changed]
    inbox_rel = [p.relative_to(config.BASE).as_posix() for p in inbox]
    for f in facts:
        f["refs"] = f["refs"] or inbox_rel   # fact mới thường trỏ inbox của lượt này
    import random
    facts = random.Random(0).sample(facts, min(int(n or os.environ.get("BRAIN_ROLES_VERIFY_N") or 5), len(facts)))
    if not facts:
        return []
    results, cost = factcheck.verify_facts(facts, role_model("verify", factcheck.verify_model()),
                                 float(budget or os.environ.get("BRAIN_ROLES_VERIFY_BUDGET") or 0.5))
    wrong = [f"- [ ] kiểm (vai verify): fact có thể sai: {textsafe.one_line(r['text'], 200)} — lý do: {r['note']} — "
             f"{datetime.now():%Y-%m-%d} key: {r['path']}:{r['line']}:{hashlib.sha1(r['text'].encode()).hexdigest()[:8]}"
             for r in results if r["verdict"] == "sai"]
    brain_kb.queue_append(config.BASE, wrong, "Kiểm mẫu fact (verify-sample)")
    util.log(f"ingest:verify {len(results)} fact, sai {len(wrong)}, est_usd={cost:.2f}")
    return results


CHECK_LATEST = "check-latest.txt"

def lint_precheck():
    """Bước chạy trước lint: `check` tất định (không LLM) ghi logs/check-latest.txt cho agent lint đọc,
    và báo cáo khoảng trống mỗi tuần vào 00-inbox/gaps-YYYY-Www.md. Lỗi ở đây không chặn lint."""
    try:
        issues = brain_kb.check(config.BASE)
        config.LOGS.mkdir(exist_ok=True)
        (config.LOGS / CHECK_LATEST).write_text(brain_kb.check_summary(issues, limit=30) + "\n", encoding="utf-8")
        new = brain_kb.write_weekly_gaps(config.BASE, config.LOGS, config.BASE / "00-inbox", verify=latest_verify())
        if new:
            util.log(f"gaps: {new.relative_to(config.BASE).as_posix()}")
        return issues
    except Exception as e:  # noqa: BLE001  check hỏng không được làm lint dừng
        util.log(f"WARN lint precheck lỗi: {e!r}")
        return []

def latest_verify():
    """Kết quả verify-sample gần nhất (không kèm từng fact), None nếu chưa có."""
    v = brain_kb.latest_verify(config.LOGS)
    return {k: x for k, x in v.items() if k != "results"} if v else None
