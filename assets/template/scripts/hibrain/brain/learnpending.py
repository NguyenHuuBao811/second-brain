"""learn: bài học (rules/) và kiến thức web (learned-*) chờ chủ brain duyệt rồi mới vào kiến thức (USER 2026-10-28).

Lượt learn để Claude ghi như thường; sau lượt, code chuyển mọi thay đổi ở file gác (GATED) sang
00-inbox/learn-pending/<id>.md và trả file đích về như cũ. Ingest chỉ đọc file nằm ngay trong 00-inbox/ nên không nạp
thư mục này. 17:45 learn-day gửi danh sách có nút Duyệt/Bỏ; DM `hoc`, `hoc duyet <id|het>`, `hoc bo <id|het>`.
Duyệt: code ghi bản chờ vào file đích (không gọi Claude), INDEX, dòng luật trong working-preferences, LOG, commit.
File đích đổi sau lúc học thì bản chờ đã lệch: bỏ, lượt sau học lại. Mục chưa duyệt không hết hạn."""
import hashlib
import re
import secrets
import time
from datetime import datetime
from pathlib import Path
from . import config, dispatching, textsafe, util

PENDING = "00-inbox/learn-pending"
PREFS = "50-knowledge/working-preferences.md"
RULES = "50-knowledge/rules/"
LOCK_POLL = 10   # giây giữa hai lần thử khoá brain-write khi job learn đang ghi

def _dir():
    return config.BASE / PENDING

def _sha(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

def _read(rel):
    p = config.BASE / rel
    return p.read_text(encoding="utf-8") if p.exists() else None

def gated_paths():
    """File chỉ vào kiến thức khi chủ brain duyệt: 50-knowledge/learned-*.md và 50-knowledge/rules/*.md."""
    kn = config.BASE / "50-knowledge"
    return sorted(p.relative_to(config.BASE).as_posix() for p in [*kn.glob("learned-*.md"), *kn.glob("rules/*.md")])

def snapshot():
    """Nội dung file gác + INDEX + working-preferences trước lượt learn (để stash so sánh và trả về)."""
    return {"files": {rel: _read(rel) for rel in gated_paths()}, "index": _read("INDEX.md") or "",
            "prefs": _read(PREFS) or ""}

def _meta(content):
    fm, body = dispatching._frontmatter(content or "")
    url = re.search(r"https?://[^\s)>\]]+", body)
    return (textsafe.one_line(fm.get("title") or "", 200), textsafe.one_line(fm.get("description") or "", 300),
            url.group(0).rstrip(".,;:") if url else "")

def items():
    """Mục đang chờ, cũ trước: [{id, target, action, base, created, title, summary, url, prefs, content}]."""
    out = []
    for p in sorted(_dir().glob("*.md")) if _dir().exists() else []:
        fm, content = dispatching._frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        if fm.get("id") and fm.get("target"):
            out.append({**fm, "content": content})
    return sorted(out, key=lambda it: (it.get("created", ""), it["id"]))

def _save(it):
    _dir().mkdir(parents=True, exist_ok=True)
    head = "".join(f"{k}: {textsafe.one_line(it.get(k) or '', 400)}\n"
                   for k in ("id", "target", "action", "base", "created", "title", "summary", "url", "prefs"))
    (_dir() / f"{it['id']}.md").write_text(f"---\n{head}---\n{it['content']}", encoding="utf-8")

def pending_titles():
    """{tên file đích: tiêu đề} của mục learned-* đang chờ, để chống học trùng."""
    return {Path(it["target"]).name: it.get("title", "") for it in items() if "/learned-" in it["target"]}

def created_today(day=None):
    day = day or f"{datetime.now():%Y-%m-%d}"
    return sum(1 for it in items() if it.get("action") == "ADD" and "/learned-" in it["target"]
               and it.get("created", "").startswith(day))

def stash(before):
    """Sau lượt learn: thay đổi ở file gác thành mục chờ, file đích trả như trước lượt (file mới thì xoá), dòng INDEX
    và dòng luật working-preferences của chúng cũng trả về. File đích đã có mục chờ thì cập nhật mục đó (giữ id/base).
    Trả [mục mới hoặc vừa cập nhật]."""
    files, now_ = before["files"], {rel: _read(rel) for rel in gated_paths()}
    pend, out = {it["target"]: it for it in items()}, []
    prefs_now = _read(PREFS) or ""
    prefs_added = [l for l in prefs_now.splitlines() if l not in set(before["prefs"].splitlines())]
    for rel in sorted(set(files) | set(now_)):
        old, new = files.get(rel), now_.get(rel)
        if old == new:
            continue
        if new is None:   # lượt learn xoá file gác: trả lại, không xoá kiến thức khi chưa duyệt
            (config.BASE / rel).write_text(old, encoding="utf-8")
            util.log(f"learn: WARN lượt learn xoá {rel}, đã trả lại")
            continue
        it = pend.get(rel) or {"id": secrets.token_hex(3), "target": rel, "action": "ADD" if old is None else "UPDATE",
                               "base": "none" if old is None else _sha(old), "created": f"{datetime.now():%Y-%m-%d %H:%M}"}
        it["content"] = new
        it["title"], it["summary"], it["url"] = _meta(new)
        if rel.startswith(RULES):
            line = next((l for l in prefs_added if f"[[{Path(rel).stem}]]" in l), "")
            it["prefs"] = line or it.get("prefs", "")
        _save(it)
        if old is None:
            (config.BASE / rel).unlink()
        else:
            (config.BASE / rel).write_text(old, encoding="utf-8")
        out.append(it)
    if out:
        _restore_lines("INDEX.md", before["index"], [f"`{it['target']}`" for it in out])
        _restore_lines(PREFS, before["prefs"], [f"[[{Path(it['target']).stem}]]" for it in out if it["target"].startswith(RULES)])
    return out

def _restore_lines(rel, before, keys):
    """Dòng chứa một trong `keys` trong file `rel`: trả về bản trước lượt (không có trước đó thì bỏ)."""
    text = _read(rel)
    if text is None or not keys:
        return
    old = {}
    for line in before.splitlines(keepends=True):
        for k in keys:
            if k in line:
                old.setdefault(k, line)
    out = []
    for line in text.splitlines(keepends=True):
        k = next((k for k in keys if k in line), None)
        if k is None:
            out.append(line)
        elif k in old:
            out.append(old.pop(k))
    (config.BASE / rel).write_text("".join(out), encoding="utf-8")

def log_lines(log_before, stashed):
    """LOG.md: bỏ dòng lượt learn vừa thêm có nhắc file đã thành mục chờ (chưa vào kiến thức), thêm dòng CHỜ DUYỆT."""
    p = config.BASE / "LOG.md"
    now_txt = p.read_text(encoding="utf-8") if p.exists() else ""
    if not stashed:
        return
    names = [Path(it["target"]).name for it in stashed]
    added = now_txt[len(log_before):] if now_txt.startswith(log_before) else ""
    kept = "".join(l for l in added.splitlines(keepends=True) if not any(n in l for n in names))
    text = (log_before if now_txt.startswith(log_before) else now_txt) + kept
    day = f"{datetime.now():%Y-%m-%d}"
    rows = [f"- {day} learn: CHỜ DUYỆT {it['action']} {it['target']} ({it.get('title') or '?'}) [{it['id']}]" for it in stashed]
    p.write_text(text + ("" if not text or text.endswith("\n") else "\n") + "\n".join(rows) + "\n", encoding="utf-8")

def _index_set(rel, content):
    """Dòng INDEX của file vừa duyệt: thay dòng cũ hoặc thêm mới (cùng format learnstore.learn_fix_index)."""
    idx = config.BASE / "INDEX.md"
    if not idx.exists():
        return
    fm, _ = dispatching._frontmatter(content)
    row = (f"- `{rel}` — {textsafe.one_line(fm.get('description') or fm.get('title') or rel, 300)} — "
           f"{fm.get('updated') or f'{datetime.now():%Y-%m-%d}'}")
    lines = idx.read_text(encoding="utf-8").splitlines()
    hit = [i for i, l in enumerate(lines) if f"`{rel}`" in l]
    if hit:
        lines[hit[0]] = row
    else:
        top = rel.split("/")[0]
        at = max((i for i, l in enumerate(lines) if l.startswith(f"- `{top}/")), default=len(lines) - 1)
        lines.insert(at + 1, row)
    idx.write_text("\n".join(lines) + "\n", encoding="utf-8")

def _prefs_add(it):
    """Luật vừa duyệt chưa có dòng trong working-preferences: thêm sau dòng luật cuối."""
    p, slug = config.BASE / PREFS, Path(it["target"]).stem
    if not p.exists() or f"[[{slug}]]" in p.read_text(encoding="utf-8"):
        return False
    lines = p.read_text(encoding="utf-8").splitlines()
    row = it.get("prefs") or f"- [[{slug}]] — {it.get('summary') or it.get('title') or slug}"
    at = max((i for i, l in enumerate(lines) if l.startswith("- [[rule-")), default=len(lines) - 1)
    lines.insert(at + 1, row)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True

def _approve(it, day):
    rel, p = it["target"], config.BASE / it["target"]
    cur = p.read_text(encoding="utf-8") if p.exists() else None
    stale = (cur is not None) if it.get("base") == "none" else (cur is None or _sha(cur) != it.get("base"))
    (_dir() / f"{it['id']}.md").unlink()
    if stale:
        return False, f"⚠️ {it.get('title') or rel}: file đã đổi sau lúc học, bỏ bản chờ (lượt sau học lại)", \
            f"- {day} learn: BỎ {rel} [{it['id']}] (lệch với file hiện tại)"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(it["content"], encoding="utf-8")
    _index_set(rel, it["content"])
    if rel.startswith(RULES):
        _prefs_add(it)
    return True, f"✅ {it.get('title') or rel}", f"- {day} learn: DUYỆT {it['action']} {rel} ({it.get('title') or '?'}) [{it['id']}] (USER)"

def _apply(op, ids):
    pend = items()
    sel = pend if ids == ["het"] else [it for it in pend if it["id"] in ids]
    missing = [] if ids == ["het"] else [i for i in ids if i not in {it["id"] for it in pend}]
    if not sel:
        return "Không có mục nào chờ duyệt." if ids == ["het"] else f"Không thấy mục chờ: {', '.join(missing)}"
    day, lines, logs, paths, n_ok = f"{datetime.now():%Y-%m-%d}", [], [], set(), 0
    for it in sel:
        paths.add(f"{PENDING}/{it['id']}.md")
        if op == "ok":
            ok, line, row = _approve(it, day)
            n_ok += ok
            if ok:
                paths.update({it["target"], "INDEX.md", PREFS})
        else:
            (_dir() / f"{it['id']}.md").unlink()
            line, row = f"✖ {it.get('title') or it['target']}", f"- {day} learn: BỎ {it['target']} [{it['id']}] (USER)"
        lines.append(line)
        logs.append(row)
    log = config.BASE / "LOG.md"
    old = log.read_text(encoding="utf-8") if log.exists() else ""
    log.write_text(old + ("" if not old or old.endswith("\n") else "\n") + "\n".join(logs) + "\n", encoding="utf-8")
    util.commit(f"learn-{'approve' if op == 'ok' else 'drop'} {datetime.now():%Y-%m-%d-%H%M} [{config.HOST}]",
                sorted(paths | {"LOG.md"}))
    head = (f"Đã duyệt {n_ok}/{len(sel)} mục vào brain" if op == "ok" else f"Đã bỏ {len(sel)} mục")
    left = len(items())
    return (head + (f", còn {left} mục chờ" if left else "") + ":\n" + "\n".join(lines)
            + (f"\nKhông thấy: {', '.join(missing)}" if missing else ""))

def apply(op, ids, wait=0):
    """Duyệt (op="ok") hoặc bỏ (op="drop") mục chờ; ids ["het"] là tất cả. Giữ khoá brain-write (job learn đang ghi
    thì chờ tối đa `wait` giây). Trả câu kết quả, None nếu hết giờ chờ mà vẫn bận."""
    ids = [str(i).strip().lower() for i in ids or [] if str(i).strip()]
    if op not in ("ok", "drop") or not ids:
        return "Cần id: hoc duyet <id> | hoc bo <id> | hoc duyet het"
    deadline = time.time() + wait
    while True:
        with util.Lock("brain-write") as lock:
            if lock is not None:
                return _apply(op, ids)
        if time.time() >= deadline:
            return None
        time.sleep(LOCK_POLL)

def _kind(it):
    return "🧠 Luật" if it["target"].startswith(RULES) else "🌐"

def line(it, n=None):
    upd = " (cập nhật)" if it.get("action") == "UPDATE" else ""
    return (f"{f'{n}. ' if n else '• '}[{it['id']}] {_kind(it)} {it.get('title') or Path(it['target']).stem}{upd}"
            + (f"\n   {it['summary']}" if it.get("summary") else "") + (f"\n   {it['url']}" if it.get("url") else ""))

HINT = "Gõ: hoc (xem) | hoc duyet <id …|het> | hoc bo <id …|het>"

def list_text(limit=15):
    pend = items()
    if not pend:
        return "Không có mục nào chờ duyệt."
    body = "\n".join(line(it, i) for i, it in enumerate(pend[:limit], 1))
    more = f"\n… còn {len(pend) - limit} mục, duyệt bớt rồi gõ `hoc` xem tiếp." if len(pend) > limit else ""
    return f"📥 Chờ a duyệt vào brain ({len(pend)} mục):\n{body}{more}\n{HINT}"

_CMD = re.compile(r"(?i)^h[oọ]c(?:\s+(duy[eệ]t|ok|b[oỏ]|drop))?(?:\s+(.+))?$")

def parse(text):
    """`hoc` → ("list", []); `hoc duyet a1 b2` / `hoc bo het` → ("ok"|"drop", ids). Không phải lệnh: None."""
    m = _CMD.match((text or "").strip())
    if not m:
        return None
    verb, rest = (m.group(1) or "").lower(), m.group(2) or ""
    if not verb:
        return ("list", []) if not rest.strip() else None
    ids = ["het" if x.lower() in ("het", "hết", "all") else x for x in re.split(r"[\s,]+", rest.strip()) if x]
    return ("ok" if verb.startswith(("duy", "ok")) else "drop"), ids
