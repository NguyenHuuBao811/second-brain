"""commit/status cho bot, lịch chạy (cron/launchd/schtasks), máy, token, doctor, init."""
import json
import os
import plistlib
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from hibrain import SCRIPTS_DIR
from . import config, larkcli, textsafe, util

# ---------------------------------------------------------------- commit / status cho bot Lark
# Claude trong DM không có lệnh git trực tiếp (git log --output, diff --no-index, commit -F đọc/ghi được file bất kỳ).
# Nó commit qua đây: code kiểm từng đường dẫn, chỉ nội dung vault, tắt hook, chỉ commit đúng file đã liệt kê.
_COMMIT_BAD_CHARS = set(":*?[]\\\n")


def commit_path_ok(f):
    if not f or f.startswith("-") or _COMMIT_BAD_CHARS & set(f):
        return None
    base = config.BASE.resolve()
    try:
        rel = (config.BASE / f).resolve().relative_to(base).as_posix()
    except ValueError:
        return None
    parts = rel.split("/")
    if rel.startswith("00-inbox/local/") or ".claude" in parts or parts[-1] in ("CLAUDE.md", "AGENTS.md"):
        return None
    if rel in config.DATA_FILES or parts[0] in config.DATA_DIRS or (parts[0] == "00-inbox" and len(parts) > 1):
        return rel
    return None


def cmd_commit(message, files):
    msg = (message or "").strip()
    if not msg or len(msg) > 500:
        sys.exit("!! cần -m \"<nội dung commit>\" (1-500 ký tự)")
    rels = [commit_path_ok(f) for f in files]
    bad = [f for f, r in zip(files, rels) if not r]
    if not files or bad:
        sys.exit(f"!! chỉ commit file nội dung vault ({', '.join(config.DATA_DIRS)}, 00-inbox/, {', '.join(config.DATA_FILES)}); "
                 f"không hợp lệ: {bad or '(trống)'}")
    if not util.git_ok():
        snap = util.snapshot(msg, rels)
        print(f"đã lưu bản chụp {snap.relative_to(config.BASE)}" if snap else "không có thay đổi")
        return 0
    for r in rels:
        if not (config.BASE / r).exists() and subprocess.run(["git", "-C", str(config.BASE), "ls-files", "--error-unmatch", "--", r],
                                                     capture_output=True).returncode != 0:
            sys.exit(f"!! không có file {r}")
    g = ["git", "-C", str(config.BASE), "-c", "core.hooksPath=/dev/null"]
    a = subprocess.run([*g, "add", "--", *rels], capture_output=True, text=True)
    c = subprocess.run([*g, "commit", "-q", "-m", msg, "--", *rels], capture_output=True, text=True) if a.returncode == 0 else a
    if c.returncode != 0:
        sys.exit(f"!! commit lỗi: {(c.stderr or c.stdout).strip()[-300:]}")
    print(subprocess.run(["git", "-C", str(config.BASE), "log", "-1", "--format=%h %s"], capture_output=True, text=True).stdout.strip())
    return 0


def cmd_status():
    if not util.git_ok():
        try:
            before = json.loads((util.snap_dir() / "state.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            before = {}
        now_all = util._scope_files(util.SNAP_SCOPE)
        for r in sorted(set(before) | set(now_all)):
            if before.get(r) != now_all.get(r):
                print(f"{'A' if r not in before else 'D' if r not in now_all else 'M'} {r}")
        return 0
    for args in (["status", "--short"], ["diff", "--stat"]):
        print(subprocess.run(["git", "-C", str(config.BASE), *args], capture_output=True, text=True).stdout.rstrip())
    return 0

def lark_dm_note(text):
    """`ghi: ...` chủ brain nhắn bot Lark (bot đã kiểm sender = OWNER_OPEN_ID): vào 00-inbox/local/ nhãn LARK-USER."""
    config.LOCAL_INBOX.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    f = config.LOCAL_INBOX / f"lark-dm-{now:%Y%m%d-%H%M%S}-{os.urandom(2).hex()}.md"
    f.write_text("<!-- Nguồn: chủ brain nhắn riêng cho bot Lark (`ghi: ...`), bot đã kiểm người gửi. "
                 "LARK-USER = lời chủ brain, xem ingest.md mục 1. -->\n\n"
                 f"### LARK-USER ({now:%Y-%m-%d %H:%M})\n{textsafe.redact(text[:4000])}\n", encoding="utf-8")
    return f

def lark_feedback_ready():
    """Record feedback được vào hàng ingest: chỉ cái trước mốc T (tin sau T dành cho đo persona-eval)."""
    files = sorted(larkcli.LARK_FEEDBACK.glob("fb-*.md")) if larkcli.LARK_FEEDBACK.exists() else []
    end = larkcli._lark_holdout_cutoff()
    if not end:
        return files
    cut = end.replace("-", "")
    return [f for f in files if f.name[3:11] < cut]


def cmd_git(repo, since):
    if not shutil.which("git"):
        sys.exit("!! máy chưa cài git: không đọc được lịch sử repo")
    repo = Path(repo).expanduser().resolve()
    out = config.BASE / "raw" / "git"
    out.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["git", "-C", str(repo), "log", f"--since={since}", "--date=short",
                        "--pretty=- %ad %an: %s"], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        sys.exit(r.stderr.strip())
    body = "\n".join(r.stdout.splitlines()[:500])
    p = out / f"{repo.name}.md"
    p.write_text(f"# git history: {repo.name} (since {since})\n\n{body}\n", encoding="utf-8")
    util.commit(f"raw git: {repo.name}", [str(p.relative_to(config.BASE))])
    print(f"{p} {body.count(chr(10)) + 1} lines")


# ---------------------------------------------------------------- scheduler
def job_schedule(job):
    """Lịch của job trên máy này: mốc trong JOBS cộng HOST_OFFSET phút."""
    s = config.JOBS[job][1]
    minute = s[-1] if job in config.FIXED_TIME_JOBS else (s[-1] + config.HOST_OFFSET) % 60
    return (*s[:-1], minute)

def job_argv(job):
    py = Path(sys.executable)
    if config.OS == "Windows" and (py.parent / "pythonw.exe").exists():
        py = py.parent / "pythonw.exe"  # không bật cửa sổ console
    model = config.JOBS[job][0]
    args = ([job] if job in ("sync", "collect", "learn-day") else ["lark", "collect"] if job == "lark"
            else ["verify-sample", "--sync"] if job == "verify" else ["run", job, "--model", model])
    return [str(py), str((SCRIPTS_DIR / "brain.py")), *args]


def cron_spec(s):
    if s[0] == "hourly":
        return f"{s[1]} * * * *"
    if s[0] == "daily":
        return f"{s[2]} {s[1]} * * *"
    return f"{s[3]} {s[2]} * * {s[1]}"


def schtasks_args(s):
    days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    if s[0] == "hourly":
        return ["/SC", "HOURLY", "/ST", f"00:{s[1]:02d}"]
    if s[0] == "daily":
        return ["/SC", "DAILY", "/ST", f"{s[1]:02d}:{s[2]:02d}"]
    return ["/SC", "WEEKLY", "/D", days[s[1]], "/ST", f"{s[2]:02d}:{s[3]:02d}"]


def launchd_interval(s):
    if s[0] == "hourly":
        return {"Minute": s[1]}
    if s[0] == "daily":
        return {"Hour": s[1], "Minute": s[2]}
    return {"Weekday": s[1], "Hour": s[2], "Minute": s[3]}


def sh(cmd, dry, **kw):
    if dry:
        print("  $", " ".join(shlex.quote(c) for c in cmd), "<<stdin>>" if "input" in kw else "")
        if "input" in kw:
            print("    " + kw["input"].replace("\n", "\n    "))
        return subprocess.CompletedProcess(cmd, 0, "", "")
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def cmd_schedule(action, jobs, dry=False, os_name=None):
    osn = os_name or config.OS
    agents = Path.home() / "Library" / "LaunchAgents"
    if action in ("install", "uninstall"):
        # gỡ mọi job cũ trước để tránh trùng
        if osn == "Darwin":
            for p in agents.glob(f"{config.LABEL}.*.plist"):
                sh(["launchctl", "unload", str(p)], dry)
                if not dry:
                    p.unlink()
        elif osn == "Linux":
            cur = "" if dry else subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
            keep = [l for l in cur.splitlines() if config.CRON_TAG not in l]
        elif osn == "Windows":
            for j in config.JOBS:
                sh(["schtasks", "/Delete", "/TN", f"{config.TASK_DIR}\\{j}", "/F"], dry)
    if action == "uninstall":
        if osn == "Linux":
            sh(["crontab", "-"], dry, input="\n".join(keep) + "\n")
        print("uninstalled")
        return 0

    if action == "status":
        if osn == "Darwin":
            print(subprocess.run(["launchctl", "list"], capture_output=True, text=True).stdout
                  .count(config.LABEL + "."), "launchd jobs loaded")
            for p in sorted(agents.glob(f"{config.LABEL}.*.plist")):
                print(" ", p.name)
        elif osn == "Linux":
            r = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
            print("\n".join(l for l in r.splitlines() if config.CRON_TAG in l) or "no cron jobs")
        else:
            for j in config.JOBS:
                r = subprocess.run(["schtasks", "/Query", "/TN", f"{config.TASK_DIR}\\{j}"], capture_output=True, text=True)
                print(j, "installed" if r.returncode == 0 else "-")
        return 0

    config.LOGS.mkdir(exist_ok=True)
    for j in jobs:
        argv, spec = job_argv(j), job_schedule(j)
        if osn == "Darwin":
            plist = {"Label": f"{config.LABEL}.{j}", "ProgramArguments": argv,
                     "WorkingDirectory": str(config.BASE), "StartCalendarInterval": launchd_interval(spec),
                     "StandardOutPath": str(config.LOGS / f"sched-{j}.log"),
                     "StandardErrorPath": str(config.LOGS / f"sched-{j}.log")}
            p = agents / f"{config.LABEL}.{j}.plist"
            if dry:
                print(f"  write {p}: {plist}")
            else:
                agents.mkdir(parents=True, exist_ok=True)
                with open(p, "wb") as f:
                    plistlib.dump(plist, f)
            sh(["launchctl", "load", str(p)], dry)
        elif osn == "Linux":
            line = (f"{cron_spec(spec)} cd {shlex.quote(str(config.BASE))} && "
                    f"{' '.join(shlex.quote(a) for a in argv)} >> {shlex.quote(str(config.LOGS / f'sched-{j}.log'))} 2>&1"
                    f" {config.CRON_TAG}{j}")
            keep.append(line)
        elif osn == "Windows":
            tr = " ".join(f'"{a}"' if " " in a or "\\" in a else a for a in argv)
            r = sh(["schtasks", "/Create", "/TN", f"{config.TASK_DIR}\\{j}", "/TR", tr, *schtasks_args(spec), "/F"], dry)
            if r.returncode != 0:
                print(f"ERROR {j}: {r.stderr.strip()}")
    if osn == "Linux":
        r = sh(["crontab", "-"], dry, input="\n".join(keep) + "\n")
        if r.returncode != 0:
            print(f"ERROR crontab: {r.stderr.strip()}")
    print(f"{'[dry] would install' if dry else 'installed'} on {osn}: {', '.join(jobs)}")
    return 0


MACHINES = config.BASE / "machines.md"
MACHINES_HEADER = ("# Machines\n\nMọi máy đều ghi được vào brain (ingest/reflect/lint/sync). Job lệch giờ theo từng máy;\n"
                   "reflect/lint chỉ một máy chạy mỗi kỳ. File này do `brain.py register` ghi, không sửa tay.\n\n"
                   "| host | os | role | since |\n|---|---|---|---|\n")


def read_machines():
    if not MACHINES.exists():
        return []
    rows = []
    for line in MACHINES.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and cells[0] not in ("host", "---"):
            rows.append(dict(zip(["host", "os", "role", "since"], cells)))
    return rows


def cmd_register():
    """Ghi máy này vào machines.md. Máy nào cũng là writer: được ingest, reflect, lint, sync."""
    if util.has_remote():
        util.pull()
    host = config.HOST
    rows = [r for r in read_machines() if r["host"] != host]
    # Bản cũ có primary/secondary: giờ mọi máy ngang quyền.
    for r in rows:
        r["role"] = "writer"
    rows.append({"host": host, "os": config.OS, "role": "writer", "since": f"{datetime.now():%Y-%m-%d}"})
    body = "".join(f"| {r['host']} | {r['os']} | {r['role']} | {r['since']} |\n" for r in rows)
    MACHINES.write_text(MACHINES_HEADER + body, encoding="utf-8")
    util.commit(f"register {host} as writer", ["machines.md"])
    util.push()
    print(f"registered {host} ({config.OS}) as writer")
    return 0

def cmd_set_token():
    """Nhập token từ `claude setup-token` mà không hiện lên màn hình hay vào lịch sử shell."""
    import getpass
    tok = getpass.getpass("Dán token từ `claude setup-token` (không hiện ký tự): ").strip()
    if not tok:
        print("!! token rỗng, không ghi")
        return 1
    if not tok.startswith("sk-ant-"):
        print("!! token không bắt đầu bằng sk-ant-, vẫn ghi nhưng hãy kiểm tra lại")
    p = config.BASE / "private" / "claude.env"
    p.parent.mkdir(exist_ok=True)
    p.write_text(f"CLAUDE_CODE_OAUTH_TOKEN={tok}\n", encoding="utf-8")
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
    print(f"saved {p}")
    return 0


def remote_writable():
    """Thử truy cập remote không tương tác, giống điều kiện khi cron/launchd chạy."""
    if not util.has_remote():
        # Một máy thì không cần remote. Chỉ báo lỗi khi đã có máy khác trong machines.md.
        multi = len(read_machines()) > 1
        return not multi, "none (một máy, không cần)" if not multi else "none, nhưng machines.md có nhiều máy"
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_SSH_COMMAND": "ssh -o BatchMode=yes"}
    r = subprocess.run(["git", "-C", str(config.BASE), "push", "--dry-run", "origin", "HEAD"],
                       capture_output=True, text=True, env=env, timeout=60)
    url = util.git("remote", "get-url", "origin").stdout.strip()
    return r.returncode == 0, url if r.returncode == 0 else f"{url}: {r.stderr.strip()[:160]}"


def scheduler_running():
    if config.OS != "Linux":
        return True, "n/a"
    r = subprocess.run(["sh", "-c", "pgrep -x cron || pgrep -x crond"], capture_output=True, text=True)
    return r.returncode == 0, "cron running" if r.returncode == 0 else "cron chưa chạy (WSL: sudo service cron start)"


def cmd_doctor():
    util.load_env()
    host = config.HOST
    me = next((r for r in read_machines() if r["host"] == host), None)
    cron_ok, cron_info = scheduler_running()
    # ok: True = OK, False = lỗi (!!), None = tuỳ chọn, chưa bật (--), không tính là lỗi.
    checks = [
        ("machine role", bool(me), f"{host}: {me['role']}" if me else f"{host} chưa register"),
        ("scheduler daemon", cron_ok, cron_info),
        ("python >= 3.9", sys.version_info >= (3, 9), sys.version.split()[0]),
        ("claude CLI", bool(util.find_claude()), util.find_claude() or "missing"),
        ("headless/settings.json", (config.BASE / "headless" / "settings.json").exists(), str(config.BASE)),
    ]
    if util.git_ok():
        rw_ok, rw_info = remote_writable()
        email = util.git("config", "user.email").stdout.strip()
        checks += [("git", True, shutil.which("git")), ("git push (non-interactive)", rw_ok, rw_info),
                   ("git user.email", bool(email), email or "chưa có: git config --global user.email <email>")]
    else:
        n = len(util.list_snapshots())
        checks.append(("git", None, ("chưa cài" if not shutil.which("git") else "brain chưa là git repo")
                       + f": lưu bằng bản chụp logs/snapshots/ ({n} bản), chỉ dùng trên máy này"))
    tok = bool(os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"))
    checks.append(("CLAUDE_CODE_OAUTH_TOKEN", True if tok else None,
                   "set" if tok else "chưa có (tuỳ chọn): job nền dùng đăng nhập Claude sẵn có nếu đọc được; "
                   "macOS hoặc job báo 401/hết phiên thì chạy `set-token`"))
    for name, ok, info in checks:
        print(f"{'OK ' if ok else '-- ' if ok is None else '!! '} {name:26} {info}")
    return 0 if all(ok is not False for _, ok, _ in checks) else 1


VAULT_DIRS = ["00-inbox/done", "10-daily", "20-projects", "25-areas", "30-people", "40-decisions", "50-knowledge/rules",
              "50-knowledge", "90-reference", "archive", "raw", "private", "logs", "eval"]


def cmd_init(target, template, name, owner, role, priorities, use_git=True):
    """Tạo brain mới từ khung. Không ghi đè: dừng nếu thư mục đích đã có file.
    Không có git (hoặc use_git=False): brain vẫn tạo, lưu bằng bản chụp logs/snapshots/ thay commit."""
    target = Path(target).expanduser().resolve()
    template = Path(template).expanduser().resolve()
    if not (template / "scripts" / "brain.py").exists():
        sys.exit(f"!! không thấy khung tại {template}")
    if target.exists() and any(target.iterdir()):
        sys.exit(f"!! {target} đã có file. Chọn thư mục trống, hoặc dùng `doctor` nếu đây là brain có sẵn.")
    use_git = use_git and bool(shutil.which("git"))
    shutil.copytree(template, target, dirs_exist_ok=True)
    today = f"{datetime.now():%Y-%m-%d}"
    values = {"{{NAME}}": name or target.name, "{{OWNER}}": owner or "(chưa điền)",
              "{{ROLE}}": role or "(chưa điền)", "{{PRIORITIES}}": priorities or "(chưa điền)",
              "{{DATE}}": today}
    for p in target.rglob("*.md"):
        text = p.read_text(encoding="utf-8")
        for k, v in values.items():
            text = text.replace(k, v)
        p.write_text(text, encoding="utf-8")
    for d in VAULT_DIRS:
        (target / d).mkdir(parents=True, exist_ok=True)
    for d in ["00-inbox/done", "10-daily", "20-projects", "25-areas", "30-people", "40-decisions", "50-knowledge/rules",
              "50-knowledge", "90-reference", "archive", "raw"]:
        (target / d / ".gitkeep").touch()
    (target / "LOG.md").write_text(f"# LOG (append-only)\n{today} init brain\n", encoding="utf-8")
    (target / "eval" / "review-queue.md").write_text("# Review queue\n", encoding="utf-8")
    (target / "eval" / "golden.jsonl").write_text("", encoding="utf-8")
    if not use_git:
        # Chụp bản đầu bằng chính brain.py của brain mới (BASE của nó), giống commit đầu khi có git.
        r = subprocess.run([sys.executable, str(target / "scripts" / "brain.py"), "commit", "-m", "init second brain",
                            "INDEX.md"], capture_output=True, text=True, encoding="utf-8")
        print(f"created {target} (không dùng git: lưu bằng bản chụp logs/snapshots/)"
              + ("" if r.returncode == 0 else f"\n!! chụp bản đầu lỗi: {(r.stderr or r.stdout).strip()[-200:]}"))
        return 0
    run = lambda *a: subprocess.run(["git", "-C", str(target), *a], capture_output=True, text=True)
    run("init", "-q")
    if not run("config", "user.email").stdout.strip():
        print("NOTE git chưa có user.email. Chạy: git config --global user.email <email>")
    run("add", "-A")
    r = run("commit", "-qm", "init second brain")
    print(f"created {target}" + ("" if r.returncode == 0 else f"\n!! commit lỗi: {r.stderr.strip()[:200]}"))
    return 0
