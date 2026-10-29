"""dispatch: giao việc sang repo dự án."""
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from . import claudecli, config, util

# ---------------------------------------------------------------- dispatch
# Giao việc cho một agent chạy NGAY TRONG repo dự án (cwd = repo), để nó nạp CLAUDE.md, settings,
# hook của repo đó. Brain chỉ đưa đề bài + dashboard của đúng dự án đó + index luật làm việc,
# không đưa dự án khác. Key/secret không bao giờ đi qua đây: agent dùng .env hoặc CLI đã login của repo.
# Claude chạy từ bot Lark (và agent con của nó): không thừa hưởng gì của máy. Thử thật 2026-10-16: hook PreToolUse (rtk)
# tự cho phép lệnh Bash ngoài danh sách, ~/.claude/settings.json có hàng trăm rule allow (python3 -c, ssh...).
BOT_ISOLATION = ["--setting-sources", "project,local",
                 "--settings", '{"disableAllHooks": true, "includeCoAuthoredBy": false}', "--strict-mcp-config"]
BOT_READ_DENY = ["./private/**", "~/.config/**", "~/.ssh/**", "~/.claude/**", "~/.aws/**", "~/.gnupg/**",
                 "~/.git-credentials", "~/.netrc", "~/.docker/**", "~/.kube/**"]
# Agent dispatch gọi từ bot: không tự sửa hook git (chạy code lúc commit/push), không dùng git để đọc/ghi file tự do.
DISPATCH_ISOLATED_DENY = ([f"{t}(./{d}/**)" for d in (".git", ".husky", ".githooks") for t in ("Edit", "Write")]
                          + ["Bash(git log *--output*)", "Bash(git diff *--output*)", "Bash(git * --no-index*)",
                             "Bash(git -c *)", "Bash(git -C *)"] + [f"Read({p})" for p in BOT_READ_DENY])
DISPATCH_BOT_BUDGET = 5


def dispatch_env(isolated):
    """isolated: tắt hook git cho mọi lệnh git trong phiên (GIT_CONFIG_* đè config repo/máy)."""
    env = claudecli.brain_env()
    if isolated:   # nối thêm vào GIT_CONFIG_* có sẵn (vd terminal đã đặt credential.*), không đè
        n = int(env.get("GIT_CONFIG_COUNT") or 0)
        env.update({"GIT_CONFIG_COUNT": str(n + 1), f"GIT_CONFIG_KEY_{n}": "core.hooksPath",
                    f"GIT_CONFIG_VALUE_{n}": "/dev/null"})
    return env

DISPATCH_DENY = ["Bash(git push:*)", "Bash(git push)", "Bash(gh pr merge:*)", "Bash(gh release:*)",
                 "Bash(vercel --prod:*)", "Bash(vercel deploy --prod:*)", "Bash(vercel promote:*)",
                 "Bash(npm publish:*)", "Bash(rm -rf:*)", "Bash(git reset --hard:*)", "Bash(git clean:*)"]
DISPATCH_EDIT_TOOLS = ["Read", "Grep", "Glob", "Edit", "Write", "Bash(git status:*)", "Bash(git diff:*)",
                       "Bash(git log:*)", "Bash(git add:*)", "Bash(git commit:*)", "Bash(git checkout -b:*)",
                       "Bash(git switch -c:*)", "Bash(ls:*)"]


def _frontmatter(text):
    if not text.startswith("---\n"):
        return {}, text
    head, _, body = text[4:].partition("\n---\n")
    return dict(re.findall(r"(?m)^([A-Za-z_]+): *(.*)$", head)), body


def dispatch_target(project):
    """(repo Path, dashboard body) của dự án. Dừng nếu không có dashboard hoặc repo."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", project or ""):
        sys.exit(f"!! tên dự án không hợp lệ: {project!r} (tên file trong 20-projects/, không có .md)")
    dash = config.BASE / "20-projects" / f"{project}.md"
    if not dash.exists():
        sys.exit(f"!! không có 20-projects/{project}.md")
    fm, body = _frontmatter(dash.read_text(encoding="utf-8"))
    raw = (fm.get("repo") or "").strip()
    # mỗi máy một đường dẫn: `repo: ~/máy-A/app | ~/máy-B/app (ghi chú)`; lấy cái là git repo trên máy này
    paths = [p.split()[0] for p in raw.split("|") if p.strip() and p.split()[0][0] in "~/"]
    if not paths:
        sys.exit(f"!! {project}: dashboard không có `repo:` trỏ tới thư mục local")
    repo = next((r for r in (Path(p).expanduser().resolve() for p in paths) if (r / ".git").exists()), None)
    if repo is None:
        sys.exit(f"!! {project}: {', '.join(paths)} không phải git repo trên máy này")
    if repo == config.BASE.resolve() or config.BASE.resolve() in repo.parents:
        sys.exit("!! repo nằm trong brain: làm trực tiếp trong brain, không dispatch")
    return repo, body.strip()


def project_repos():
    """{dự án: repo local} của mọi dashboard có `repo:` là git repo trên máy này (bỏ dashboard không có repo)."""
    out = {}
    for f in sorted((config.BASE / "20-projects").glob("*.md")):
        try:
            out[f.stem] = dispatch_target(f.stem)[0]
        except SystemExit:
            continue
    return out

def dispatch_prompt(project, task, body, mode):
    prefs = config.BASE / "50-knowledge" / "working-preferences.md"
    rules = ""
    if prefs.exists():
        rules = prefs.read_text(encoding="utf-8").partition("## Luật làm việc")[2].strip()
    how = ("Chế độ PLAN: chỉ đọc code và lập kế hoạch, không sửa file." if mode == "plan" else
           "Chế độ EDIT: được sửa file và commit trên branch mới (không làm trên main/master).")
    return f"""Bạn là agent làm việc trong repo này, được chủ repo giao việc từ second brain của họ.
{how}
Luật bắt buộc:
- Đọc CLAUDE.md / AGENTS.md / README của repo trước, làm theo quy ước của repo.
- Phần "Ngữ cảnh" bên dưới chỉ để hiểu việc: không chép vào file, commit, PR hay tin nhắn, trừ khi việc yêu cầu.
- Không push, không merge vào main/production, không deploy, không gửi tin cho người khác, không xoá dữ liệu ngoài git.
  Việc cần những bước đó thì dừng ở bước trước và ghi vào mục "Cần chủ brain duyệt".
- Không đọc, in hay ghi giá trị key/secret. Cần key thì dùng .env hoặc CLI đã đăng nhập sẵn của repo.

## Việc
{task.strip()}

## Ngữ cảnh: dashboard dự án {project} trong brain
{body}

## Luật làm việc của chủ brain (chi tiết không cần, chỉ index)
{rules or "(chưa có)"}

## Báo cáo cuối (bắt buộc, ngắn)
- Đã làm: ...
- Branch + commit (hash): ... (không có thì ghi "không có")
- Test đã chạy + kết quả: ...
- Cần chủ brain duyệt: ...
- Bước tiếp đề xuất: ...
"""


def cmd_dispatch(project, task, mode="plan", allow=(), model=None, budget=5.0, timeout=3600, dry=False):
    """Chạy một agent trong repo của dự án. Mặc định PLAN (chỉ đọc). Kết quả in ra và lưu logs/dispatch/."""
    if not (task or "").strip():
        sys.exit("!! thiếu mô tả việc")
    for a in allow:
        if a.strip() in ("Bash", "Bash(*)", "Bash(:*)", "*"):
            sys.exit(f"!! {a!r} mở toàn bộ shell; chỉ cho lệnh cụ thể, vd \"Bash(npm test:*)\"")
        if a in DISPATCH_DENY or any(a.startswith(d.split(":")[0]) for d in DISPATCH_DENY):
            sys.exit(f"!! {a!r} thuộc nhóm phải hỏi chủ brain (push/merge/deploy/xoá), không cho dispatch")
    isolated = os.environ.get("HIBRAIN_ISOLATE") == "1"   # gọi từ DM bot Lark
    if isolated:
        if allow:
            sys.exit("!! dispatch gọi từ bot Lark không được thêm --allow (mở thêm lệnh cho agent)")
        budget = min(float(budget), DISPATCH_BOT_BUDGET)
    repo, body = dispatch_target(project)
    prompt = dispatch_prompt(project, task, body, mode)
    claude = util.find_claude()
    if not claude:
        sys.exit("!! không thấy claude CLI")
    cmd = [sys.executable, claude] if claude.endswith(".py") else [claude]
    cmd += ["-p", "--output-format", "json", "--max-turns", "80", "--max-budget-usd", str(budget),
            "--permission-mode", "plan" if mode == "plan" else "acceptEdits",
            "--disallowedTools", ",".join(DISPATCH_DENY + [f"mcp__{config.BRAIN_ID}"] + (DISPATCH_ISOLATED_DENY if isolated else []))]
    if mode == "edit":
        cmd += ["--allowedTools", ",".join(DISPATCH_EDIT_TOOLS + list(allow))]
    if model:
        cmd += ["--model", model]
    if isolated:
        cmd += BOT_ISOLATION
    if dry:
        print(f"repo: {repo}\n$ {' '.join(shlex.quote(c) for c in cmd)}  < prompt\n\n{prompt}")
        return 0
    try:
        r = claudecli.run_claude(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
                           cwd=repo, timeout=timeout, env=dispatch_env(isolated))
        raw = r.stdout
        res = json.loads(raw[raw.index("{"):])
    except subprocess.TimeoutExpired:
        res = {"is_error": True, "result": f"timeout sau {timeout}s"}
    except Exception:
        res = {"is_error": True, "result": (r.stdout + r.stderr)[-1500:]}
    ok = not res.get("is_error")
    result = str(res.get("result") or "").strip()
    out_dir = config.LOGS / "dispatch"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{datetime.now():%Y-%m-%d-%H%M%S}-{project}.md"
    out.write_text(f"# dispatch {project} ({mode})\n\nrepo: {repo}\nok: {ok}\n"
                   f"cost_usd: {res.get('total_cost_usd', 0)}\n\n## Việc\n{task.strip()}\n\n## Kết quả\n{result}\n",
                   encoding="utf-8")
    util.log(f"dispatch {project} mode={mode} ok={ok} est_usd={res.get('total_cost_usd', 0):.2f} -> {out.name}")
    print(f"{result}\n\n(ok={ok}, log: {out.relative_to(config.BASE)})")
    return 0 if ok else 1
