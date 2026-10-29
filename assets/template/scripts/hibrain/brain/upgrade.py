"""locate / upgrade brain theo khung template."""
import os
import plistlib
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from . import config, dispatching, migrate

# ---------------------------------------------------------------- locate / upgrade
# Skill second-brain chạy hai lệnh này từ khung template trước khi dựng: máy đã có brain thì nâng cấp
# brain đó theo khung mới nhất thay vì tạo bản thứ hai. Không phụ thuộc BASE: cả hai nhận đường dẫn rõ ràng.
UPGRADE_CONTROL_GLOBS = ["scripts/brain.py", "scripts/hibrain/__init__.py", "scripts/hibrain/brain/*.py", "scripts/brain_mcp.py", "scripts/brain_kb.py","headless/settings.json", "CLAUDE.md",
                         "GEMINI.md", "README.md", "prompts/*.md", ".claude/skills/*/SKILL.md"]
UPGRADE_STARTERS = ["50-knowledge/working-preferences.md"]
UPGRADE_DIRS = ["00-inbox/done", "10-daily", "20-projects", "25-areas", "30-people", "40-decisions",
                "50-knowledge", "50-knowledge/rules", "90-reference", "archive", "raw", "eval"]
UPGRADE_AGENTS_PHRASES = ["50-knowledge/rules/", "25-areas/", "status: active", "/dispatch", "Không ghi key"]


def _is_brain(d):
    return all((d / f).exists() for f in ("scripts/brain.py", "AGENTS.md", "INDEX.md"))


def locate_brains(home=None):
    """Brain có trên máy: lấy từ lịch job đã cài, rồi quét thư mục home (sâu 2 cấp)."""
    home = Path(home or Path.home())
    found = {}
    agents = home / "Library" / "LaunchAgents"
    for pl in sorted(agents.glob("com.secondbrain.*.plist")) if agents.is_dir() else []:
        try:
            wd = plistlib.loads(pl.read_bytes()).get("WorkingDirectory")
        except Exception:
            continue
        if wd and _is_brain(Path(wd)):
            found.setdefault(str(Path(wd).resolve()), set()).add(pl.name.split(".")[3] if pl.name.count(".") >= 4 else pl.name)
    if shutil.which("crontab"):
        cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
        for m in re.finditer(r"cd (\S+) && .*# secondbrain:[^:]+:(\w+)", cron):
            d = Path(shlex.split(m.group(1))[0])
            if _is_brain(d):
                found.setdefault(str(d.resolve()), set()).add(m.group(2))
    skip = {"Library", "node_modules", "Applications", ".Trash", "anaconda3", "miniconda3"}
    for d1 in sorted(home.iterdir()) if home.is_dir() else []:
        if d1.name in skip or not d1.is_dir():
            continue
        for d in [d1, *sorted(x for x in d1.iterdir() if x.is_dir())] if os.access(d1, os.R_OK) else [d1]:
            try:
                if d.name not in skip and _is_brain(d):
                    found.setdefault(str(d.resolve()), set())
            except OSError:
                pass
    return {k: sorted(v) for k, v in found.items()}


def locate_lite_brains(home=None):
    """Brain second-brain-lite trên máy (thư mục home sâu 2 cấp): cấu trúc khác, chuyển sang bằng `migrate`."""
    home, out = Path(home or Path.home()), []
    for d1 in sorted(home.iterdir()) if home.is_dir() else []:
        if not d1.is_dir() or d1.name.startswith(".") or d1.name in ("Library", "node_modules"):
            continue
        try:
            for d in [d1, *sorted(x for x in d1.iterdir() if x.is_dir() and not x.name.startswith("."))]:
                if migrate._is_lite_brain(d) and not _is_brain(d):
                    out.append(str(d.resolve()))
        except OSError:
            pass
    return out


def _brain_name(target):
    first = (target / "AGENTS.md").read_text(encoding="utf-8").splitlines()[:1]
    m = re.match(r"#\s*(.+?)\s+—", first[0]) if first else None
    return m.group(1) if m else target.name


def _fill(text, name, today):
    return (text.replace("{{NAME}}", name).replace("{{DATE}}", today)
            .replace("{{OWNER}}", "(chưa điền)").replace("{{ROLE}}", "(chưa điền)").replace("{{PRIORITIES}}", "(chưa điền)"))


def upgrade_brain(target, template, apply=False, home=None, skip_update=False):
    """So brain với khung. Trả list (trạng thái, mục, chi tiết).
    OK = đã đúng; ADD = thiếu, sẽ/đã thêm; UPDATE = file điều khiển khác khung, sẽ/đã thay (bản cũ vào
    private/upgrade-backup/); MANUAL = cần Claude cùng người dùng làm; NOTE = khuyến nghị cấu hình máy.
    Không bao giờ ghi đè dữ liệu (fact, dự án, luật, AGENTS.md, CRITICAL.md)."""
    target, template = Path(target).expanduser().resolve(), Path(template).expanduser().resolve()
    if not _is_brain(target):
        sys.exit(f"!! {target} không phải brain (thiếu scripts/brain.py, AGENTS.md hoặc INDEX.md)")
    name, today = _brain_name(target), f"{datetime.now():%Y-%m-%d}"
    backup = target / "private" / "upgrade-backup" / f"{datetime.now():%Y%m%d-%H%M%S}"
    rep = []
    for d in UPGRADE_DIRS:
        if (target / d).is_dir():
            continue
        rep.append(("ADD", d + "/", "thư mục mới của khung"))
        if apply:
            (target / d).mkdir(parents=True, exist_ok=True)
            (target / d / ".gitkeep").touch()
    for pat in UPGRADE_CONTROL_GLOBS:
        for src in sorted(template.glob(pat)):
            rel = src.relative_to(template).as_posix()
            dst = target / rel
            new = _fill(src.read_text(encoding="utf-8"), name, today) if src.suffix == ".md" else src.read_text(encoding="utf-8")
            if not dst.exists():
                rep.append(("ADD", rel, "file điều khiển chưa có"))
            elif dst.read_text(encoding="utf-8") != new:
                if skip_update:
                    rep.append(("SKIP", rel, "khác khung, giữ nguyên (--skip-update)"))
                    continue
                rep.append(("UPDATE", rel, "khác khung; bản cũ lưu vào private/upgrade-backup/"))
                if apply:
                    (backup / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dst, backup / rel)
            else:
                rep.append(("OK", rel, ""))
                continue
            if apply:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(new, encoding="utf-8")
    for rel in UPGRADE_STARTERS:
        if not (target / rel).exists():
            rep.append(("ADD", rel, "file khởi đầu"))
            if apply:
                (target / rel).parent.mkdir(parents=True, exist_ok=True)
                (target / rel).write_text(_fill((template / rel).read_text(encoding="utf-8"), name, today), encoding="utf-8")
    gi_t = [l for l in (template / ".gitignore").read_text(encoding="utf-8").splitlines() if l.strip()]
    gi_path = target / ".gitignore"
    gi = gi_path.read_text(encoding="utf-8").splitlines() if gi_path.exists() else []
    miss = [l for l in gi_t if l not in gi]
    if miss:
        rep.append(("ADD", ".gitignore", "thêm dòng: " + ", ".join(miss)))
        if apply:
            gi_path.write_text("\n".join(gi + miss) + "\n", encoding="utf-8")
    idx_path = target / "INDEX.md"
    idx = idx_path.read_text(encoding="utf-8")
    heads = [l for l in (template / "INDEX.md").read_text(encoding="utf-8").splitlines() if l.startswith("## ")]
    miss = [h for h in heads if h not in idx.splitlines()]
    if miss:
        rep.append(("ADD", "INDEX.md", "thêm mục: " + ", ".join(miss)))
        if apply:
            idx_path.write_text(idx.rstrip("\n") + "\n\n" + "\n".join(miss) + "\n", encoding="utf-8")
    # Phần cần phán đoán: báo để Claude làm cùng người dùng (references/upgrade.md).
    agents = (target / "AGENTS.md").read_text(encoding="utf-8")
    t_heads = [l for l in (template / "AGENTS.md").read_text(encoding="utf-8").splitlines() if l.startswith("## ")]
    miss = [h for h in t_heads if h not in agents.splitlines()] + [p for p in UPGRADE_AGENTS_PHRASES if p not in agents]
    rep.append(("MANUAL" if miss else "OK", "AGENTS.md", ("gộp từ khung: " + "; ".join(miss)) if miss else ""))
    projects = sorted((target / "20-projects").glob("*.md")) if (target / "20-projects").is_dir() else []
    old = [p.stem for p in projects if not {"status", "area", "repo"} <= set(dispatching._frontmatter(p.read_text(encoding="utf-8"))[0])]
    rep.append(("MANUAL" if old else "OK", "20-projects/", f"chưa ở dạng dashboard: {', '.join(old)}" if old else f"{len(projects)} dashboard"))
    areas = sorted((target / "25-areas").glob("*.md")) if (target / "25-areas").is_dir() else []
    rep.append(("OK" if areas else "MANUAL", "25-areas/", f"{len(areas)} area" if areas else "chưa có area: hỏi người dùng các mảng trách nhiệm"))
    prefs = target / "50-knowledge" / "working-preferences.md"
    if prefs.exists():
        sec = prefs.read_text(encoding="utf-8").partition("## Luật làm việc")[2]
        legacy = [l for l in sec.splitlines() if l.startswith("- ") and not l.startswith("- [[rule-")]
        rep.append(("MANUAL" if legacy else "OK", "50-knowledge/rules/",
                    f"{len(legacy)} luật còn dạng 1 dòng trong working-preferences.md, cần tách thành file có Why" if legacy else ""))
    # Cấu hình máy: chỉ khuyến nghị, không tự sửa.
    home = Path(home or Path.home())
    bid = re.sub(r"[^a-z0-9]+", "-", target.name.lower()).strip("-") or "brain"
    if config.OS == "Darwin":
        have = {pl.name.split(".")[-2] for pl in (home / "Library" / "LaunchAgents").glob(f"com.secondbrain.{bid}.*.plist")}
        want = set(config.JOBS) - {"sync"}
        if have and want - have:
            rep.append(("NOTE", "lịch job", f"thiếu {', '.join(sorted(want - have))}: chạy lại `schedule install --jobs ...` trong brain"))
    allow = target / "private" / "collect-projects.txt"
    if not allow.exists() or not [l for l in allow.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]:
        rep.append(("NOTE", "collect --allow", "chưa cho phép repo nào: brain không học được từ chat ở repo khác"))
    cj = home / ".claude.json"
    mcp = cj.exists() and "brain_mcp.py" in cj.read_text(encoding="utf-8", errors="ignore")
    if not mcp:
        rep.append(("NOTE", "MCP cấp user", "chưa nối brain vào các dự án khác (Bước 6c)"))
    return rep


def cmd_upgrade(target, template, apply, skip_update=False):
    rep = upgrade_brain(target, template, apply, skip_update=skip_update)
    for st, item, detail in rep:
        if st != "OK":
            print(f"{st:7} {item:38} {detail}")
    n = {k: sum(1 for r in rep if r[0] == k) for k in ("OK", "ADD", "UPDATE", "SKIP", "MANUAL", "NOTE")}
    print(f"\n{n['OK']} OK, {n['ADD']} ADD, {n['UPDATE']} UPDATE, {n['SKIP']} SKIP, {n['MANUAL']} MANUAL, {n['NOTE']} NOTE"
          + ("" if apply else "  (dry-run: thêm --apply để ghi ADD/UPDATE)"))
    return 0
