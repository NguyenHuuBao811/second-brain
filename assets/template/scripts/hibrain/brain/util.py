"""Tiện ích chung: log, git, khoá, pull/push/commit, tìm claude, sync."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from . import config

# ---------------------------------------------------------------- helpers
def now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def log(msg):
    config.LOGS.mkdir(exist_ok=True)
    line = f"{now()} [{config.HOST}] {msg}"
    if sys.stdout:  # pythonw.exe trên Windows không có stdout
        print(line)
    with open(config.LOGS / "run.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def git_ok():
    """Máy có git và brain là git repo. Không có thì brain vẫn chạy: `commit` thành bản chụp logs/snapshots/."""
    return bool(shutil.which("git")) and (config.BASE / ".git").exists()


def git(*args):
    if not git_ok():
        return subprocess.CompletedProcess(["git", *args], 1, "", "không có git")
    return subprocess.run(["git", "-C", str(config.BASE), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def has_remote():
    return bool(git("remote").stdout.strip())


def load_env():
    """Nạp private/claude.env (dòng KEY=VALUE hoặc export KEY=VALUE). Không ghi đè biến đã có."""
    p = config.BASE / "private" / "claude.env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.removeprefix("export ").split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def find_claude():
    env_bin = os.environ.get("CLAUDE_BIN")
    if env_bin and Path(env_bin).exists():
        return env_bin
    found = shutil.which("claude")
    if found:
        return found
    home = Path.home()
    nvm = sorted(home.glob(".nvm/versions/node/*/bin/claude"), reverse=True)
    candidates = [*nvm, home / ".local/bin/claude", home / ".claude/local/claude",
                  Path("/opt/homebrew/bin/claude"), Path("/usr/local/bin/claude"),
                  home / ".npm-global/bin/claude", home / ".local/bin/claude.exe",
                  Path(os.environ.get("APPDATA", "")) / "npm/claude.cmd"]
    return next((str(c) for c in candidates if c.exists()), None)


class Lock:
    """Khoá theo job, tự gỡ khoá cũ hơn 2 giờ (job trước bị kill)."""

    def __init__(self, name):
        self.path = config.LOGS / f"{name}.lock"
        self.acquired = False

    def __enter__(self):
        config.LOGS.mkdir(exist_ok=True)
        if self.path.exists() and time.time() - self.path.stat().st_mtime > 7200:
            self.path.unlink()
        try:
            os.close(os.open(self.path, os.O_CREAT | os.O_EXCL))
        except FileExistsError:
            return None
        self.acquired = True
        return self

    def __exit__(self, *exc):
        if self.acquired:
            self.path.unlink(missing_ok=True)


def pull():
    if not has_remote():
        return True
    before = git("rev-parse", "HEAD").stdout.strip()
    r = git("pull", "--rebase", "--autostash")
    if r.returncode != 0:
        git("rebase", "--abort")
        # Nhiều máy cùng ghi: hai máy sửa cùng một dòng (thường là INDEX.md). Thử lại, phần
        # trùng giữ bản của máy này (vừa ghi xong, mới hơn); phần không trùng gộp cả hai.
        r = git("pull", "--rebase", "--autostash", "-X", "theirs")
        if r.returncode != 0:
            git("rebase", "--abort")
            log(f"WARN git pull failed: {r.stderr.strip()[:300]}")
            return False
        log("NOTE git pull có xung đột, phần trùng giữ bản của máy này")
    changed = git("diff", "--name-only", before, "HEAD", "--", *config.CONTROL).stdout.strip()
    if changed:
        log(f"NOTE control files updated from remote: {changed.replace(chr(10), ', ')}")
    return True


def push():
    if not has_remote():
        return
    if git("push").returncode != 0 and pull():
        r = git("push")
        if r.returncode != 0:
            log(f"WARN git push failed: {r.stderr.strip()[:300]}")


def commit(msg, paths):
    """Commit chỉ các path được liệt kê, không quét file người khác đã stage.

    Một path là thư mục tồn tại nhưng không có file nào thay đổi (vd 30-people/ rỗng) sẽ không
    được staged: `git commit -- <paths gốc>` sẽ báo "pathspec did not match" và lỗi im lặng mãi
    mãi, nên commit chỉ các file thực sự có thay đổi đã stage.
    Brain không có git: chụp bản .zip (snapshot) thay commit.
    """
    if not git_ok():
        return snapshot(msg, paths) is not None
    existing = [p for p in paths if (config.BASE / p).exists() or git("ls-files", p).stdout]
    if not existing:
        return False
    git("add", "--", *existing)
    staged = git("diff", "--cached", "--name-only", "--", *existing).stdout.strip().splitlines()
    if not staged:
        return False
    r = git("commit", "-qm", msg, "--", *staged)
    if r.returncode != 0:
        log(f"WARN git commit failed: {r.stderr.strip()[:300]}")
    return r.returncode == 0


# ---------------------------------------------------------------- không git: bản chụp (giống second-brain-lite)
# Máy không cài git: mỗi lần "commit" là một file .zip chụp phần dữ liệu (logs/snapshots/, giữ SNAP_KEEP bản) và một
# dòng nhật ký logs/nap.jsonl (giờ, việc, file đổi). `history` liệt kê, `restore <số>` khôi phục (tự chụp bản hiện tại
# trước nên hoàn tác được). Không đồng bộ nhiều máy: muốn vậy thì cài git.
SNAP_KEEP = 90
SNAP_SCOPE = ["00-inbox", *config.DATA_DIRS, *config.DATA_FILES, "machines.md"]

def snap_dir():
    return config.LOGS / "snapshots"

def _scope_files(paths):
    out = {}
    for item in paths:
        p = config.BASE / item
        files = [p] if p.is_file() else sorted(f for f in p.rglob("*") if f.is_file()) if p.is_dir() else []
        for f in files:
            rel = f.relative_to(config.BASE).as_posix()
            if "/local/" not in f"/{rel}" and not f.name.endswith(".lock"):
                out[rel] = hashlib.sha1(f.read_bytes()).hexdigest()
    return out

def event(kind, note="", files=()):
    """Một dòng nhật ký logs/nap.jsonl. Lỗi ghi nhật ký không làm hỏng lệnh chính."""
    try:
        config.LOGS.mkdir(exist_ok=True)
        with open(config.LOGS / "nap.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"time": f"{datetime.now():%Y-%m-%d %H:%M}", "host": config.HOST, "kind": kind,
                                "note": " ".join(str(note).split())[:200], "files": list(files)[:50]},
                               ensure_ascii=False) + "\n")
    except OSError:
        pass

def snapshot(msg, paths=None, force=False):
    """Chụp SNAP_SCOPE vào logs/snapshots/<số>-<giờ>.zip khi `paths` có file đổi so với bản trước (force: luôn chụp).
    Trả đường dẫn bản chụp, hoặc None nếu không có gì đổi."""
    import zipfile
    d = snap_dir()
    d.mkdir(parents=True, exist_ok=True)
    state_p = d / "state.json"
    try:
        before = json.loads(state_p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        before = {}
    now_all = _scope_files(SNAP_SCOPE)
    inside = lambda r: not paths or any(r == p.rstrip("/") or r.startswith(p.rstrip("/") + "/") for p in paths)
    changed = sorted(r for r in set(now_all) | set(before) if inside(r) and before.get(r) != now_all.get(r))
    if not changed and not force:
        return None
    seq = max((int(p.name.split("-", 1)[0]) for p in d.glob("*.zip") if p.name.split("-", 1)[0].isdigit()), default=0) + 1
    out = d / f"{seq:05d}-{datetime.now():%Y-%m-%d-%H%M}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("_snapshot.json", json.dumps({"time": f"{datetime.now():%Y-%m-%d %H:%M}", "note": msg, "host": config.HOST,
                                                 "changed": changed[:200]}, ensure_ascii=False))
        for rel in sorted(now_all):
            z.write(config.BASE / rel, rel)
    state_p.write_text(json.dumps(now_all, sort_keys=True), encoding="utf-8")
    for old in sorted(d.glob("*.zip"))[:-SNAP_KEEP]:
        old.unlink()
    event("luu", msg, changed)
    return out

def list_snapshots():
    """[(số, path, meta)] mới nhất trước; số 1 = bản mới nhất."""
    import zipfile
    out = []
    for p in sorted(snap_dir().glob("*.zip"), reverse=True) if snap_dir().is_dir() else []:
        try:
            with zipfile.ZipFile(p) as z:
                meta = json.loads(z.read("_snapshot.json"))
        except (zipfile.BadZipFile, KeyError, ValueError, OSError):
            continue
        out.append((len(out) + 1, p, meta))
    return out

def cmd_history(limit=20):
    if git_ok():
        print(git("log", f"-{limit}", "--format=%h %ad %s", "--date=format:%Y-%m-%d %H:%M").stdout.rstrip()
              or "(chưa có commit)")
        print("Hoàn tác: git revert <hash>")
        return 0
    snaps = list_snapshots()
    for n, p, meta in snaps[:limit]:
        print(f"{n:3}. {meta.get('time', '?')}  {meta.get('note', '')}  ({len(meta.get('changed') or [])} file đổi)")
    print("Khôi phục: brain.py restore <số>  (tự chụp bản hiện tại trước, nên hoàn tác được)" if snaps
          else "(chưa có bản chụp nào)")
    return 0

def cmd_restore(number):
    """Đưa phần dữ liệu về bản chụp <số> (theo `history`). Chỉ cho brain không có git (có git thì git revert)."""
    import zipfile
    if git_ok():
        sys.exit("!! brain này có git: hoàn tác bằng `git revert <hash>` (xem `brain.py history`)")
    snaps = {n: (p, meta) for n, p, meta in list_snapshots()}
    if number not in snaps:
        sys.exit(f"!! không có bản số {number} (xem `brain.py history`)")
    path, meta = snaps[number]
    before = snapshot(f"trước khi khôi phục về bản {meta.get('time')}", force=True)
    base = config.BASE.resolve()
    with zipfile.ZipFile(path) as z:
        keep = [n for n in z.namelist() if n != "_snapshot.json" and not n.endswith("/")]
        for rel in keep:
            if base not in (config.BASE / rel).resolve().parents:
                sys.exit("!! bản chụp có đường dẫn lạ, dừng")
        for rel in set(_scope_files(SNAP_SCOPE)) - set(keep):
            (config.BASE / rel).unlink()
        for rel in keep:
            (config.BASE / rel).parent.mkdir(parents=True, exist_ok=True)
            (config.BASE / rel).write_bytes(z.read(rel))
    (snap_dir() / "state.json").write_text(json.dumps(_scope_files(SNAP_SCOPE), sort_keys=True), encoding="utf-8")
    event("khoi-phuc", f"về bản {meta.get('time')} · {meta.get('note', '')}")
    print(f"Đã khôi phục về bản {meta.get('time')} ({meta.get('note', '')}). "
          f"Bản trước khi khôi phục: {before.relative_to(config.BASE) if before else '(không đổi)'}")
    return 0


def cmd_sync():
    """Đẩy file mới trong 00-inbox lên remote và kéo brain mới về. Máy nào cũng chạy."""
    with Lock("sync") as lock:
        if lock is None:
            return 0
        if not has_remote():
            log("sync skipped: repo chưa có remote")
            return 0
        commit(f"inbox from {config.HOST} [{config.HOST}]", ["00-inbox"])
        pull()
        push()
        return 0
