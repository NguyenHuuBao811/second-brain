#!/usr/bin/env python3
"""Phần tất định (không gọi LLM) của brain: nhật ký hỏi đáp, gaps, hạn dùng fact, check, tìm kiếm FTS5.
Chỉ dùng thư viện chuẩn Python 3.9+. Mọi hàm nhận `base` (thư mục vault) để test được trên fixture.
brain.py nối các hàm này vào CLI, MCP (brain_mcp.py) và bot Lark (lark_bot.py).
"""
import hashlib
import json
import os
import re
import sqlite3
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

# Thư mục fact (cần frontmatter đủ, tính mồ côi/stale) và phần agent được đọc/tìm.
FACT_DIRS = ["20-projects", "25-areas", "30-people", "40-decisions", "50-knowledge"]
READABLE = ["AGENTS.md", "CRITICAL.md", "INDEX.md", "LOG.md", "indexes", "10-daily", "20-projects", "25-areas",
            "30-people", "40-decisions", "50-knowledge", "90-reference", "archive", "docs"]
REQUIRED_FM = ("type", "title", "description", "updated")
MAX_LINES = 200
# Hạn dùng theo loại tin (USER 2026-10-23): tiến độ 14 ngày, cấu hình/server/số liệu 30 ngày, luật/quyết định không hết.
TTL_PROGRESS, TTL_CONFIG = 14, 30
NO_EXPIRE_TYPES = {"rule", "decision", "hub", "area", "reference"}
CONFIG_TAGS = {"server", "config", "cau-hinh", "metric", "so-lieu", "infra", "env", "deploy"}


def today():
    return date.today()


def parse_date(s):
    m = re.match(r"\s*(\d{4}-\d{2}-\d{2})", str(s or ""))
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d").date() if m else None
    except ValueError:
        return None


def fold(text):
    """Chữ thường, bỏ dấu (đ → d): so khớp tiếng Việt có/không dấu."""
    t = unicodedata.normalize("NFD", str(text).lower().replace("đ", "d"))
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def frontmatter(text):
    """(dict, body, số dòng frontmatter). Giá trị là chuỗi thô; list đọc bằng fm_list."""
    if not text.startswith("---\n"):
        return {}, text, 0
    head, sep, body = text[4:].partition("\n---\n")
    if not sep:
        return {}, text, 0
    return dict(re.findall(r"(?m)^([A-Za-z_]+): *(.*)$", head)), body, head.count("\n") + 2


def fm_list(value):
    """`[a, b]`, `[[a]], [[b]]` hoặc `a, b` thành [a, b]."""
    v = str(value or "").strip()
    links = re.findall(r"\[\[([^\]|#]+)", v)
    if links:
        return [x.strip() for x in links]
    return [x.strip().strip("'\"") for x in v.strip("[]").split(",") if x.strip().strip("'\"")]


def rel(base, p):
    return Path(p).relative_to(base).as_posix()


def vault_files(base, dirs=None):
    """File .md trong phần đã tinh luyện (không private/, raw/, inbox, logs)."""
    base = Path(base)
    for item in dirs or READABLE:
        p = base / item
        if p.is_file():
            yield p
        elif p.is_dir():
            yield from sorted(f for f in p.rglob("*.md") if f.is_file() and "private" not in f.parts)


def read(p):
    return Path(p).read_text(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- 1.1 nhật ký hỏi đáp + gaps
QA_LOG = "hoi-dap.jsonl"


def log_question(logs_dir, question, files_read=(), answered=True, duration_s=None, tokens=None, source="",
                 redact=lambda s: s):
    """Một câu hỏi tới brain thành một dòng {ts, question, files_read, answered, duration_s, tokens, source}.
    Ghi lỗi thì bỏ qua: nhật ký không bao giờ làm hỏng câu trả lời."""
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "question": redact(str(question))[:500],
           "files_read": sorted({str(f) for f in files_read if f})[:30], "answered": bool(answered),
           "duration_s": round(duration_s, 2) if duration_s is not None else None, "tokens": tokens,
           "source": source}
    try:
        Path(logs_dir).mkdir(parents=True, exist_ok=True)
        with open(Path(logs_dir) / QA_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return rec


def read_qa_log(logs_dir, days=None):
    p = Path(logs_dir) / QA_LOG
    since = datetime.now() - timedelta(days=days) if days else None
    rows = []
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    for line in lines:
        try:
            r = json.loads(line)
            if since and datetime.fromisoformat(r["ts"]) < since:
                continue
            rows.append(r)
        except (ValueError, KeyError, TypeError):
            continue
    return rows


_STOP = set("la gi cua cho co khong va voi nao the sao nhu nay do roi duoc mot cac nhung trong ve tu den "
            "da dang se bao nhieu ai o dau khi thi ma hay hoac a e anh em chi oi nhe a ạ".split()) | {
    "the", "what", "is", "a", "an", "of", "to", "how", "and", "for", "in", "on"}
_AREA_HINTS = [("20-projects", "du an"), ("30-people", "nguoi"), ("40-decisions", "quyet dinh"),
               ("50-knowledge/rules", "luat"), ("50-knowledge", "kien thuc")]


def keywords(text, n=3):
    words = [w for w in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", fold(text)) if w not in _STOP]
    return [w for w, _ in Counter(words).most_common(n)]


def project_gaps(base):
    """Dashboard 20-projects có mục ghi "Không có trong brain": [(file, [mục])]."""
    out = []
    for p in vault_files(base, ["20-projects"]):
        secs, cur = [], None
        for line in read(p).splitlines():
            if line.startswith("## "):
                cur = line[3:].strip()
            elif cur and "không có trong brain" in line.lower() and cur not in secs:
                secs.append(cur)
        if secs:
            out.append((rel(base, p), secs))
    return out


def gaps_report(base, logs_dir, days=7, verify=None):
    """Markdown: câu không trả lời được (nhóm theo mảng/từ khoá) + dự án có mục trống + tỷ lệ sai kiểm mẫu."""
    rows = read_qa_log(logs_dir, days)
    miss = [r for r in rows if not r.get("answered")]
    groups = defaultdict(list)
    for r in miss:
        files = r.get("files_read") or []
        area = next((name for d, name in _AREA_HINTS for f in files if str(f).startswith(d)), None)
        key = area or (keywords(r["question"], 1) or ["khác"])[0]
        groups[key].append(r["question"])
    d = today().isoformat()
    lines = ["---", "type: report", f"title: Khoảng trống brain {d}",
             f"description: Câu hỏi brain không trả lời được trong {days} ngày và dự án có mục trống (brain.py gaps)",
             f"updated: {d}", "tags: [gaps, eval]", "---", "",
             f"# Khoảng trống brain ({days} ngày tới {d})", "",
             f"- Câu hỏi: {len(rows)}, không trả lời được: {len(miss)}"
             + (f" ({100 * len(miss) // len(rows)}%)" if rows else ""), ""]
    lines.append("## Câu không trả lời được")
    if not groups:
        lines.append("- Không có.")
    for key, qs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"- **{key}** ({len(qs)}): " + " | ".join(dict.fromkeys(q[:120] for q in qs[:5])))
    lines += ["", "## Dự án có mục \"Không có trong brain\""]
    pg = project_gaps(base)
    lines += [f"- `{f}`: {', '.join(s)}" for f, s in pg] or ["- Không có."]
    if verify:
        lines += ["", "## Kiểm mẫu fact (verify-sample)",
                  f"- {verify.get('date')}: {verify.get('checked', 0)} fact, sai {verify.get('wrong', 0)}"
                  f" ({verify.get('wrong_rate', 0):.0%}), không kiểm chứng được {verify.get('unverifiable', 0)}"]
    return "\n".join(lines) + "\n"


def write_weekly_gaps(base, logs_dir, inbox, verify=None, when=None):
    """Mỗi tuần ISO một file 00-inbox/gaps-YYYY-Www.md; đã có thì thôi. Trả đường dẫn mới hoặc None."""
    when = when or today()
    y, w, _ = when.isocalendar()
    p = Path(inbox) / f"gaps-{y}-W{w:02d}.md"
    if p.exists():
        return None
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(gaps_report(base, logs_dir, 7, verify), encoding="utf-8")
    return p


# ---------------------------------------------------------------- 1.2 hạn dùng fact
def ttl_days(fm, path=""):
    """Số ngày fact còn dùng được, None = không hết hạn. `ttl_days:` trong frontmatter thắng."""
    if str(fm.get("ttl_days", "")).strip().isdigit():
        return int(fm["ttl_days"])
    typ = str(fm.get("type", "")).strip().lower()
    tags = {fold(t) for t in fm_list(fm.get("tags"))}
    if typ in NO_EXPIRE_TYPES or "/rules/" in path or path.startswith("40-decisions/"):
        return None
    if typ == "project" or path.startswith("20-projects/"):
        return TTL_PROGRESS
    if tags & CONFIG_TAGS or typ in ("config", "server", "metric"):
        return TTL_CONFIG
    return None


def stale_info(fm, path="", now=None):
    """(stale?, hạn) cho file có last_verified. Không có last_verified (file cũ) thì không gắn cờ."""
    lv = parse_date(fm.get("last_verified"))
    ttl = ttl_days(fm, path)
    if not lv or ttl is None:
        return False, None
    due = lv + timedelta(days=ttl)
    return (now or today()) > due, due


def backfill_last_verified(base, apply=False):
    """File fact thiếu last_verified: thêm last_verified = updated. Trả danh sách file (dry khi apply=False)."""
    changed = []
    for p in vault_files(base, FACT_DIRS):
        text = read(p)
        fm, _, _ = frontmatter(text)
        if not fm or fm.get("last_verified") or not parse_date(fm.get("updated")):
            continue
        changed.append(rel(base, p))
        if apply:
            new = re.sub(r"(?m)^(updated: *.*)$", lambda m: f"{m.group(1)}\nlast_verified: "
                         f"{parse_date(fm['updated']).isoformat()}", text, count=1)
            p.write_text(new, encoding="utf-8")
    return changed


# ---------------------------------------------------------------- 1.3 check tất định
_LINK_RE = re.compile(r"\[\[([^\]\n]+?)\]\]")
_INDEX_RE = re.compile(r"^- `([^`]+)`")


def strip_code(text):
    return re.sub(r"```.*?```", "", re.sub(r"`[^`\n]*`", "", text, flags=re.S), flags=re.S)


def links_of(text):
    """Đích [[...]] trong thân (bỏ code) và trong related: tên file không .md, bỏ |alias và #mục."""
    fm, body, _ = frontmatter(text)
    out = [m.split("|")[0].split("#")[0].strip() for m in _LINK_RE.findall(strip_code(body))]
    out += fm_list(fm.get("related")) + fm_list(fm.get("superseded_by"))
    return [x[:-3] if x.endswith(".md") else x for x in out if x]


def index_entries(base):
    """{path: dòng} từ INDEX.md và mọi chỉ mục con indexes/*.md."""
    base = Path(base)
    out = {}
    for p in [base / "INDEX.md", *sorted((base / "indexes").glob("*.md"))]:
        if p.exists():
            for line in read(p).splitlines():
                m = _INDEX_RE.match(line)
                if m:
                    out[m.group(1)] = line
    return out


def all_md(base):
    base = Path(base)
    skip = {"private", "raw", "logs", ".git", "node_modules", "00-inbox", "skills", "web", ".claude"}
    return [p for p in base.rglob("*.md") if not (set(p.relative_to(base).parts[:-1]) & skip)]


def check(base, now=None):
    """Danh sách issue {kind, path, msg, block}. block=True là lỗi chặn (mã thoát ≠ 0)."""
    base = Path(base)
    issues = []
    add = lambda kind, path, msg, block=False: issues.append({"kind": kind, "path": path, "msg": msg, "block": block})
    files = all_md(base)
    stems = {p.stem for p in files} | {rel(base, p)[:-3] for p in files}
    inbound = defaultdict(set)
    texts = {}
    for p in files:
        r = rel(base, p)
        texts[r] = t = read(p)
        for target in links_of(t):
            inbound[target.split("/")[-1]].add(r)
            if target not in stems and target.split("/")[-1] not in stems:
                add("dead-link", r, f"[[{target}]] không trỏ tới file nào", True)
    idx = index_entries(base)
    for path in idx:
        if not (base / path).exists():
            add("index-missing-file", "INDEX.md", f"`{path}` không tồn tại", True)
    for p in vault_files(base, FACT_DIRS):
        r = rel(base, p)
        t = texts.get(r) or read(p)
        fm, _, _ = frontmatter(t)
        miss = [k for k in REQUIRED_FM if not str(fm.get(k, "")).strip()]
        if miss:
            add("frontmatter", r, "thiếu " + ", ".join(miss), True)
        if fm and not fm_list(fm.get("related")) and not r.startswith("20-projects/") and fm.get("type") not in ("qa", "hub"):
            add("no-related", r, "thiếu related")
        stale, due = stale_info(fm, r, now)
        if stale:
            add("stale", r, f"quá hạn từ {due} (last_verified {fm.get('last_verified')})")
        n = t.count("\n") + 1
        if n > MAX_LINES:
            add("too-long", r, f"{n} dòng > {MAX_LINES}")
        in_index = r in idx
        if not in_index:
            add("not-in-index", r, "không có dòng INDEX")
        if not in_index and not (inbound.get(p.stem, set()) - {r}):
            add("orphan", r, "không file nào link tới và không có trong INDEX")
    for qa in qa_issues(base, now):
        issues.append(qa)
    issues += hub_issues(base)
    for c in find_conflicts(base):
        add("conflict", c["new"]["path"], f"{c['entity']}/{c['attr']}: \"{c['new']['value'][:60]}\" ≠ "
            f"\"{c['old']['value'][:60]}\" ({c['old']['path']})")
    return issues


def check_summary(issues, limit=8):
    by = defaultdict(list)
    for i in issues:
        by[i["kind"]].append(i)
    n_block = sum(i["block"] for i in issues)
    lines = [f"check: {len(issues)} vấn đề, {n_block} lỗi chặn"]
    for kind, items in sorted(by.items(), key=lambda kv: (not kv[1][0]["block"], kv[0])):
        lines.append(f"{'!!' if items[0]['block'] else '--'} {kind}: {len(items)}")
        lines += [f"   {i['path']}: {i['msg']}" for i in items[:limit]]
        if len(items) > limit:
            lines.append(f"   ... +{len(items) - limit}")
    return "\n".join(lines)


# ---------------------------------------------------------------- 1.4 tìm kiếm SQLite FTS5 (BM25)
INDEX_DB = Path(os.environ.get("BRAIN_INDEX_DB") or Path.home() / ".cache" / "hibrain" / "index.db")


def fts5_available():
    try:
        c = sqlite3.connect(":memory:")
        c.execute("CREATE VIRTUAL TABLE t USING fts5(a)")
        c.close()
        return True
    except sqlite3.Error:
        return False


def _db(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(path), timeout=10)
    c.execute("CREATE TABLE IF NOT EXISTS docs(base TEXT, path TEXT, mtime INTEGER, size INTEGER, sha TEXT,"
              " PRIMARY KEY(base, path))")
    c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS lines USING fts5(path, text, base UNINDEXED, line UNINDEXED,"
              " tokenize='unicode61 remove_diacritics 2')")
    return c


def refresh_index(base, db_path=None):
    """Dựng lại phần index của file đã đổi (so mtime/size, rồi SHA-256). Trả số file đã nạp lại."""
    base = Path(base).resolve()
    b = str(base)
    c = _db(db_path or INDEX_DB)
    with c:
        known = {r[0]: r[1:] for r in c.execute("SELECT path, mtime, size, sha FROM docs WHERE base=?", (b,))}
        seen, n = set(), 0
        for p in vault_files(base):
            r = rel(base, p)
            seen.add(r)
            st = p.stat()
            old = known.get(r)
            if old and old[0] == st.st_mtime_ns and old[1] == st.st_size:
                continue
            data = p.read_bytes()
            sha = hashlib.sha256(data).hexdigest()
            if old and old[2] == sha:
                c.execute("UPDATE docs SET mtime=?, size=? WHERE base=? AND path=?", (st.st_mtime_ns, st.st_size, b, r))
                continue
            c.execute("DELETE FROM lines WHERE base=? AND path=?", (b, r))
            c.executemany("INSERT INTO lines(path, text, base, line) VALUES (?,?,?,?)",
                          [(r, line, b, i) for i, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1)
                           if line.strip()])
            c.execute("INSERT OR REPLACE INTO docs VALUES (?,?,?,?,?)", (b, r, st.st_mtime_ns, st.st_size, sha))
            n += 1
        for r in set(known) - seen:
            c.execute("DELETE FROM lines WHERE base=? AND path=?", (b, r))
            c.execute("DELETE FROM docs WHERE base=? AND path=?", (b, r))
    c.close()
    return n


def _fts_query(query, any_word=False):
    words = [w for w in re.findall(r"\w+", query) if w]
    return (" OR " if any_word else " ").join('"' + w.replace('"', "") + '"*' for w in words)


def search_fts(base, query, limit=20, db_path=None, prefix=None, any_word=False):
    """[{path, line, text, score}] xếp theo BM25 (score cao = khớp hơn). Mọi từ phải có trong dòng hoặc tên file
    (any_word=True: chỉ cần một từ, dùng tìm câu hỏi tương tự)."""
    q = _fts_query(query, any_word)
    if not q:
        return []
    refresh_index(base, db_path)
    b = str(Path(base).resolve())
    c = _db(db_path or INDEX_DB)
    try:
        sql = ("SELECT path, line, text, bm25(lines, 2.0, 1.0) AS s FROM lines WHERE lines MATCH ? AND base=?"
               + (" AND path LIKE ?" if prefix else "") + " ORDER BY s LIMIT ?")
        args = [q, b] + ([prefix + "%"] if prefix else []) + [limit]
        rows = c.execute(sql, args).fetchall()
    finally:
        c.close()
    return [{"path": p, "line": int(i), "text": t.strip()[:300], "score": round(-s, 3)} for p, i, t, s in rows]


def search_grep(base, query, limit=20, prefix=None):
    """Fallback không có FTS5: như brain_search cũ (mọi từ có trong dòng hoặc tên file)."""
    words = [w.lower() for w in query.split() if w.strip()]
    if not words:
        return []
    hits = []
    for f in vault_files(base):
        r = rel(base, f)
        if prefix and not r.startswith(prefix):
            continue
        for i, line in enumerate(read(f).splitlines(), 1):
            if all(w in f"{r} {line}".lower() for w in words):
                hits.append({"path": r, "line": i, "text": line.strip()[:300], "score": 0.0})
                if len(hits) >= limit:
                    return hits
    return hits


def search(base, query, limit=20, db_path=None, prefix=None):
    if os.environ.get("BRAIN_FTS", "1") != "0" and fts5_available():
        try:
            hits = search_fts(base, query, limit, db_path, prefix)
            if hits:
                return hits
        except sqlite3.Error:
            pass
    return search_grep(base, query, limit, prefix)


# ---------------------------------------------------------------- 2.1 INDEX nhiều tầng
INDEX_CORE_MAX = 17_000
INDEX_DIR = "indexes"
MANDATORY = ["CRITICAL.md", "50-knowledge/working-preferences.md", "50-knowledge/owner-model.md",
             "30-people/team-map.md"]
_AREA_OF = [("20-projects/", "projects", "dashboard dự án"), ("25-areas/", "areas", "area dài hạn"),
            ("30-people/", "people", "công ty, team-map"), ("40-decisions/", "decisions", "quyết định"),
            ("50-knowledge/rules/", "rules", "luật làm việc"), ("50-knowledge/qa/", "qa", "câu trả lời đã lưu"),
            ("50-knowledge/hubs/", "hubs", "trang trung tâm"), ("10-daily/", "daily", "nhật ký ngày"),
            ("archive/", "archive", "bản cũ đã thay")]


def index_area(path, knowledge_groups=None):
    for prefix, name, _ in _AREA_OF:
        if path.startswith(prefix):
            return name
    if path.startswith("50-knowledge/"):
        g = Path(path).stem.split("-")[0]
        return f"knowledge-{g}" if g in (knowledge_groups or ()) else "knowledge-khac"
    return "docs"


def build_indexes(base, apply=False, today_s=None):
    """Tách INDEX: lõi (< 17KB: file bắt buộc + danh sách chỉ mục con) và indexes/index-<mảng>.md.
    Đọc cả INDEX.md lẫn chỉ mục con có sẵn nên chạy lại được (dòng ở INDEX.md mới hơn thì thắng).
    Trả {tên file: nội dung}; chỉ ghi khi apply=True."""
    base = Path(base)
    d = today_s or today().isoformat()
    entries = {}
    for p in [*sorted((base / INDEX_DIR).glob("*.md")), base / "INDEX.md"]:
        if p.exists():
            for line in read(p).splitlines():
                m = _INDEX_RE.match(line)
                if m and not m.group(1).startswith(INDEX_DIR + "/"):
                    entries[m.group(1)] = line
    stems = Counter(Path(k).stem.split("-")[0] for k in entries
                    if k.startswith("50-knowledge/") and index_area(k) == "knowledge-khac")
    groups = {g for g, n in stems.items() if n >= 3}
    by = defaultdict(list)
    for path, line in entries.items():
        by[index_area(path, groups)].append(line)
    desc = {name: what for _, name, what in _AREA_OF}
    out, rows = {}, []
    for name in sorted(by):
        lines = sorted(by[name])
        what = desc.get(name) or ("tài liệu, eval, kế hoạch" if name == "docs" else
                                  f"kiến thức nhóm {name.split('-', 1)[1]}")
        out[f"{INDEX_DIR}/index-{name}.md"] = (
            f"# Chỉ mục {name} — {what}\n\nSinh bởi `brain.py index --build` ({d}). Sửa dòng ở đây hoặc thêm vào "
            f"INDEX.md rồi chạy lại build. Format: `path` — description — updated\n\n" + "\n".join(lines) + "\n")
        sample = ", ".join(Path(_INDEX_RE.match(l).group(1)).stem for l in lines[:4])
        rows.append(f"- `{INDEX_DIR}/index-{name}.md` — {what}: {len(lines)} file ({sample}…) — {d}")
    core = ["# INDEX lõi — đọc mỗi phiên. Format: `path` — description — updated", "",
            "Chỉ mục chi tiết theo mảng ở `indexes/` (mở đúng mảng cần): `python3 scripts/brain.py index <mảng>`.",
            "File mới: thêm dòng vào đây hoặc chỉ mục con của mảng; `brain.py index --build` xếp lại.", "",
            "## Bắt buộc"] + [entries[m] for m in MANDATORY if m in entries] + ["", "## Chỉ mục con"] + rows
    out["INDEX.md"] = "\n".join(core) + "\n"
    if apply:
        (base / INDEX_DIR).mkdir(exist_ok=True)
        for old in (base / INDEX_DIR).glob("index-*.md"):
            if f"{INDEX_DIR}/{old.name}" not in out:
                old.unlink()
        for name, text in out.items():
            (base / name).write_text(text, encoding="utf-8")
    return out


def show_index(base, area):
    p = Path(base) / INDEX_DIR / f"index-{re.sub(r'[^a-z0-9-]+', '', area.lower())}.md"
    if p.exists():
        return read(p)
    names = sorted(x.stem[len("index-"):] for x in (Path(base) / INDEX_DIR).glob("index-*.md"))
    raise ValueError(f"không có chỉ mục {area}. Có: {', '.join(names) or '(chưa build: brain.py index --build)'}")


# ---------------------------------------------------------------- 2.2 chọn fact để kiểm mẫu
_MID_RE = re.compile(r"\bom_[A-Za-z0-9_-]{6,}")
_REF_RE = re.compile(r"(?<![\w/])((?:[\w.-]+/)*[\w.-]+\.(?:md|jsonl|txt))\b")
_QUOTE_RE = re.compile(r"[\"“]([^\"”\n]{6,300})[\"”]")


def fact_lines(base):
    """Dòng fact có nguồn trong thư mục fact (bỏ dòng có invalid_at)."""
    for p in vault_files(base, FACT_DIRS):
        r = rel(base, p)
        for i, line in enumerate(read(p).splitlines(), 1):
            if "nguồn:" in line.lower() and "invalid_at" not in line:
                refs = [x for x in _REF_RE.findall(line) if x != Path(r).name]
                yield {"path": r, "line": i, "text": line.strip()[:600], "mids": _MID_RE.findall(line),
                       "refs": refs, "quote": (_QUOTE_RE.findall(line) or [""])[0]}


def sample_facts(base, n=10, seed=None):
    import random
    facts = [f for f in fact_lines(base) if f["mids"] or f["refs"]]
    return random.Random(seed).sample(facts, min(n, len(facts)))


def _excerpt(text, needles, width=700):
    t = fold(text)
    for nd in needles:
        k = t.find(fold(nd)[:60]) if nd else -1
        if k >= 0:
            return text[max(0, k - width // 2): k + width]
    return ""


def source_excerpt(base, fact, extra_dirs=()):
    """Đoạn bản gốc quanh trích dẫn/message_id của fact, hoặc "" nếu không tìm được bản gốc."""
    base = Path(base)
    needles = [*fact["mids"], fact["quote"], *keywords(fact["text"], 3)]
    for ref in fact["refs"]:
        for root in (base, *map(Path, extra_dirs)):
            if not root.is_dir():
                continue
            hits = [root / ref] if (root / ref).is_file() else list(root.rglob(Path(ref).name))[:3]
            for h in hits:
                ex = _excerpt(read(h), needles)
                if ex:
                    return f"[{h.name}]\n{ex}"
    for mid in fact["mids"]:
        for root in [base / "00-inbox", base / "raw", *map(Path, extra_dirs)]:
            if not root.is_dir():
                continue
            for h in root.rglob("*.md"):
                t = read(h)
                if mid in t:
                    return f"[{h.name}]\n{_excerpt(t, [mid])}"
    return ""


def verify_summary(results, model="", cost=0.0, when=None):
    wrong = sum(r["verdict"] == "sai" for r in results)
    unv = sum(r["verdict"] == "khong_kiem_chung" for r in results)
    checked = len(results) - unv
    return {"date": (when or today()).isoformat(), "model": model, "checked": checked, "wrong": wrong,
            "unverifiable": unv, "wrong_rate": wrong / checked if checked else 0.0, "cost": round(cost, 4),
            "results": results}


def latest_verify(logs_dir):
    files = sorted(Path(logs_dir).glob("verify-*.json"))
    try:
        return json.loads(files[-1].read_text(encoding="utf-8")) if files else None
    except (OSError, ValueError):
        return None


def queue_append(base, lines, marker):
    """Thêm dòng vào eval/review-queue.md (mục `## <marker>`); bỏ dòng đã có (so phần sau ` key: `)."""
    q = Path(base) / "eval" / "review-queue.md"
    q.parent.mkdir(parents=True, exist_ok=True)
    text = read(q) if q.exists() else ""
    new = [l for l in lines if (l.split(" key: ")[-1] if " key: " in l else l) not in text]
    if not new:
        return []
    head = f"## {marker}"
    if head not in text:
        text = text.rstrip("\n") + ("\n\n" if text else "") + head + "\n"
    i = text.index(head) + len(head) + 1
    text = text[:i] + "".join(l + "\n" for l in new) + text[i:]
    q.write_text(text, encoding="utf-8")
    return new


# ---------------------------------------------------------------- 2.3 mâu thuẫn tự phát hiện
_CLAIM_RE = re.compile(r"^\s*[-*] (?:\*\*)?(?P<attr>[^:*\n—`\[]{2,40}?)(?:\*\*)?:\s*(?P<val>.+?)\s+—\s+as of\s+"
                       r"(?P<d>\d{4}-\d{2}-\d{2})(?P<rest>.*)$")


def fact_claims(base):
    """Fact dạng `- <thuộc tính>: <giá trị> — as of YYYY-MM-DD, nguồn: ...`. Entity = `entity:` trong
    frontmatter, không có thì tên file (dashboard/người/hệ thống). Bỏ dòng invalid_at/gạch."""
    for p in vault_files(base, FACT_DIRS):
        r = rel(base, p)
        text = read(p)
        f, _, _ = frontmatter(text)
        if f.get("invalid_at"):
            continue
        entity = (f.get("entity") or p.stem).strip()
        for i, line in enumerate(text.splitlines(), 1):
            m = _CLAIM_RE.match(line)
            if not m or "invalid_at" in line or "~~" in line:
                continue
            yield {"entity": entity, "attr": m.group("attr").strip(), "value": m.group("val").strip(),
                   "as_of": m.group("d"), "path": r, "line": i, "source": m.group("rest").strip(" ,")}


def _norm_val(v):
    return " ".join(re.findall(r"[a-z0-9]+", fold(v)))


def find_conflicts(base):
    """Cùng (entity, thuộc tính), giá trị khác nhau: [{entity, attr, new, old}] (new = as of mới hơn)."""
    groups = defaultdict(list)
    for c in fact_claims(base):
        groups[(fold(c["entity"]), fold(c["attr"]))].append(c)
    out = []
    for _, items in sorted(groups.items()):
        if len({_norm_val(c["value"]) for c in items}) < 2:
            continue
        items.sort(key=lambda c: (c["as_of"], c["path"]), reverse=True)
        new = items[0]
        old = next(c for c in items if _norm_val(c["value"]) != _norm_val(new["value"]))
        out.append({"entity": new["entity"], "attr": new["attr"], "new": new, "old": old})
    return out


def conflict_lines(conflicts):
    lines = []
    for c in conflicts:
        n, o = c["new"], c["old"]
        keep = "mới hơn" if n["as_of"] != o["as_of"] else "cùng ngày, chủ brain chọn"
        lines.append(f"- [ ] mâu thuẫn {c['entity']}/{c['attr']}: \"{n['value'][:120]}\" ({n['path']}:{n['line']}, "
                     f"as of {n['as_of']}) ≠ \"{o['value'][:120]}\" ({o['path']}:{o['line']}, as of {o['as_of']}) — "
                     f"đề xuất giữ: \"{n['value'][:60]}\" ({keep}), bản kia thêm invalid_at — "
                     f"key: {fold(c['entity'])}|{fold(c['attr'])}|{_norm_val(n['value'])}|{_norm_val(o['value'])}")
    return lines


# ---------------------------------------------------------------- 2.4 kho raw ngoài git + manifest
RAW_MANIFEST = "raw-manifest.jsonl"


def raw_archive_dir():
    return Path(os.environ.get("BRAIN_RAW_ARCHIVE") or Path.home() / ".cache" / "hibrain" / "raw-archive").expanduser()


def raw_keep_days():
    try:
        return int(os.environ.get("BRAIN_RAW_KEEP_DAYS") or 180)
    except ValueError:
        return 180


def file_version(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:12]
    except OSError:
        return "unknown"


def archive_raw(src, outputs=(), ingest_version="", archive=None):
    """Chép bản gốc đã nạp vào kho (theo ngày, tên kèm SHA-256) và thêm một dòng manifest. Trả raw_id."""
    archive = Path(archive or raw_archive_dir())
    data = Path(src).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    now = datetime.now()
    raw_id = f"{now:%Y%m%d}-{sha[:12]}"
    dest = archive / f"{now:%Y-%m-%d}" / f"{raw_id}-{Path(src).name}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        dest.write_bytes(data)
    row = {"raw_id": raw_id, "sha256": sha, "ingested_at": now.isoformat(timespec="seconds"),
           "ingest_version": ingest_version, "outputs": sorted(set(outputs))[:50], "name": Path(src).name,
           "file": dest.relative_to(archive).as_posix()}
    with open(archive / RAW_MANIFEST, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return raw_id


def raw_manifest(archive=None):
    rows = []
    try:
        lines = (Path(archive or raw_archive_dir()) / RAW_MANIFEST).read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    for line in lines:
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def reingest_select(raw_id=None, since=None, archive=None):
    rows = raw_manifest(archive)
    if raw_id:
        return [r for r in rows if r["raw_id"] == raw_id]
    d = parse_date(since)
    return [r for r in rows if d and parse_date(r.get("ingested_at")) and parse_date(r["ingested_at"]) >= d]


def reingest_apply(rows, inbox_local, archive=None):
    """Chép bản gốc (đã kiểm SHA-256) về 00-inbox/local để ingest chạy lại. Trả [(raw_id, kết quả)]."""
    archive = Path(archive or raw_archive_dir())
    out = []
    for r in rows:
        src = archive / r["file"]
        if not src.exists():
            out.append((r["raw_id"], "mất bản gốc (đã quá hạn giữ?)"))
            continue
        data = src.read_bytes()
        if hashlib.sha256(data).hexdigest() != r["sha256"]:
            out.append((r["raw_id"], "SHA-256 lệch, bỏ qua"))
            continue
        dest = Path(inbox_local) / f"reingest-{r['raw_id']}-{r['name']}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        out.append((r["raw_id"], dest.name))
    return out


def raw_expired(days=None, archive=None, now=None):
    """Bản gốc quá hạn giữ (mặc định 180 ngày). Chỉ liệt kê; xoá cần `--apply` (xác nhận của chủ brain)."""
    limit = (now or datetime.now()) - timedelta(days=days or raw_keep_days())
    archive = Path(archive or raw_archive_dir())
    return [r for r in raw_manifest(archive) if datetime.fromisoformat(r["ingested_at"]) < limit
            and (archive / r["file"]).exists()]


# ---------------------------------------------------------------- 3.1 lưu câu trả lời (50-knowledge/qa)
QA_DIR = "50-knowledge/qa"
QA_TTL = 14
QA_SIMILAR = 0.6
_SENSITIVE_RE = re.compile(r"(?i)lương|thưởng|mật khẩu|password|passwd|token|secret|api[ _-]?key|\bsđt\b|số điện thoại"
                           r"|địa chỉ nhà|cccd|cmnd|hộ chiếu|ngân hàng|số tài khoản|hợp đồng|bảng giá|báo giá|giá bao nhiêu"
                           r"|sức khỏe|sức khoẻ|bệnh|riêng tư|cá nhân|người yêu|gia đình|\[REDACTED\]")
_NO_ANSWER_RE = re.compile(r"(?i)không có trong brain|chưa có|không rõ|không biết|NEED_OWNER")


def qa_per_day():
    try:
        return int(os.environ.get("BRAIN_QA_PER_DAY") or 10)
    except ValueError:
        return 10


def slugify(text, n=60):
    return "-".join(re.findall(r"[a-z0-9]+", fold(text)))[:n].strip("-") or "cau-hoi"


def _qwords(text):
    return {w for w in re.findall(r"[a-z0-9]+", fold(text)) if w not in _STOP and len(w) > 1}


def similarity(a, b):
    x, y = _qwords(a), _qwords(b)
    return len(x & y) / len(x | y) if x and y else 0.0


def sources_hash(base, sources):
    h = hashlib.sha256()
    for s in sorted(sources):
        p = Path(base) / s
        h.update(s.encode() + b"\0" + (p.read_bytes() if p.is_file() else b"<missing>"))
    return h.hexdigest()[:16]


def qa_files(base):
    return sorted((Path(base) / QA_DIR).glob("*.md"))


def qa_save(base, question, answer, sources, certainty="cao", ttl=None, now=None):
    """Lưu/cập nhật 50-knowledge/qa/<slug>.md. Chỉ câu có nguồn (file vault có thật), đã chắc (không 'thấp'),
    không cá nhân/nhạy cảm, không quá BRAIN_QA_PER_DAY file mới/ngày. Trả (đường dẫn tương đối | None, lý do)."""
    base = Path(base)
    d = now or today()
    srcs = sorted({s for s in sources if s and not s.startswith(QA_DIR) and (base / s).is_file()})
    if not srcs:
        return None, "không có nguồn"
    if fold(certainty).startswith("thap"):
        return None, "chưa chắc"
    if _SENSITIVE_RE.search(question) or _SENSITIVE_RE.search(answer):
        return None, "nhạy cảm/cá nhân"
    if _NO_ANSWER_RE.search(answer):
        return None, "không trả lời được"
    p = base / QA_DIR / f"{slugify(question)}.md"
    created = d.isoformat()
    if p.exists():
        created = frontmatter(read(p))[0].get("created") or created
    elif sum(frontmatter(read(f))[0].get("created") == d.isoformat() for f in qa_files(base)) >= qa_per_day():
        return None, f"quá {qa_per_day()} file qa mới/ngày"
    q1 = " ".join(str(question).split())
    fm_text = ["---", "type: qa", f"title: {q1[:100]}", f"description: Hỏi đáp đã lưu: {q1[:150]}",
               f"updated: {d.isoformat()}", f"last_verified: {d.isoformat()}",
               f"expires: {(d + timedelta(days=ttl or QA_TTL)).isoformat()}", f"created: {created}",
               f"certainty: {certainty}", "sources: [" + ", ".join(srcs) + "]",
               f"source_hash: {sources_hash(base, srcs)}", "tags: [qa]",
               "related: [" + ", ".join(Path(s).stem for s in srcs) + "]", "---", ""]
    body = ["## Câu hỏi", q1, "", "## Trả lời", answer.strip(), "", "## Nguồn"] + [f"- `{s}`" for s in srcs]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(fm_text + body) + "\n", encoding="utf-8")
    return rel(base, p), "ok"


def qa_state(base, p, now=None):
    """(còn dùng được?, lý do) của một file qa: quá hạn hoặc nguồn đã đổi thì phải kiểm lại."""
    f, _, _ = frontmatter(read(p))
    exp = parse_date(f.get("expires"))
    if not exp or (now or today()) > exp:
        return False, f"quá hạn {f.get('expires') or '?'}"
    if sources_hash(base, fm_list(f.get("sources"))) != f.get("source_hash"):
        return False, "nguồn đã đổi"
    return True, "còn hạn"


def qa_lookup(base, question, db_path=None, now=None):
    """Bản qa cho câu hỏi tương tự (FTS5 chọn ứng viên, rồi so từ khoá ≥ QA_SIMILAR), hoặc None.
    Trả {path, question, answer, fresh, reason, score}."""
    base = Path(base)
    if not (base / QA_DIR).is_dir():
        return None
    cands = qa_files(base)
    if fts5_available() and os.environ.get("BRAIN_FTS", "1") != "0":
        try:
            hits = search_fts(base, question, 40, db_path, prefix=QA_DIR + "/", any_word=True)
            cands = [base / p for p in dict.fromkeys(h["path"] for h in hits)] or cands
        except sqlite3.Error:
            pass
    best = None
    for p in cands:
        f, body, _ = frontmatter(read(p))
        s = similarity(question, f.get("title", ""))
        if s >= QA_SIMILAR and (not best or s > best["score"]):
            ans = body.split("## Trả lời", 1)[-1].split("## Nguồn", 1)[0].strip()
            best = {"path": rel(base, p), "question": f.get("title", ""), "answer": ans, "score": round(s, 2)}
    if best:
        best["fresh"], best["reason"] = qa_state(base, base / best["path"], now)
    return best


def qa_issues(base, now=None):
    out = []
    for p in qa_files(base):
        ok, why = qa_state(base, p, now)
        if not ok:
            out.append({"kind": "qa-stale", "path": rel(base, p), "msg": why, "block": False})
    return out


def qa_prune(base, apply=False, grace_days=30, now=None):
    """File qa quá hạn hơn grace_days ngày hoặc mất hết nguồn: liệt kê, apply=True thì xoá (file trong git)."""
    d = now or today()
    out = []
    for p in qa_files(base):
        f, _, _ = frontmatter(read(p))
        exp = parse_date(f.get("expires"))
        gone = not any((Path(base) / s).is_file() for s in fm_list(f.get("sources")))
        if gone or not exp or d > exp + timedelta(days=grace_days):
            out.append(rel(base, p))
            if apply:
                p.unlink()
    return out


# ---------------------------------------------------------------- đo: chấm câu hỏi vàng tất định
def load_golden(base, sets=("golden", "golden-lark")):
    rows = []
    for name in sets:
        p = Path(base) / "eval" / f"{name}.jsonl"
        if not p.exists():
            continue
        for line in read(p).splitlines():
            try:
                rows.append({**json.loads(line), "set": name})
            except ValueError:
                continue
    return rows


def score_eval(row, answer, cited):
    """{hit, correct, answered}. hit: mọi expected_pages có trong cited (đuôi `/` = bất kỳ file trong thư mục).
    Câu bẫy (expected rỗng): đúng khi trả lời "không có trong brain". correct: ≥ 50% từ khoá đáp án chuẩn có trong
    câu trả lời; đáp án chuẩn rỗng thì None."""
    cited = [str(c).strip() for c in cited or []]
    exp = row.get("expected_pages") or []
    says_no = bool(_NO_ANSWER_RE.search(answer or ""))
    if not exp:
        return {"hit": says_no, "correct": says_no, "answered": not says_no}
    hit = all(any(c.startswith(e) if e.endswith("/") else c == e for c in cited) for e in exp)
    want = _qwords(row.get("answer") or "")
    correct = (len(want & _qwords(answer or "")) / len(want) >= 0.5) if want else None
    return {"hit": hit, "correct": correct, "answered": not says_no}


def eval_report(rows, model, when=None):
    d = (when or today()).isoformat()
    def pct(xs):
        xs = [x for x in xs if x is not None]
        return f"{100 * sum(xs) / len(xs):.0f}%" if xs else "-"
    lines = ["---", "type: report", f"title: Eval tự động {d}", "description: brain.py eval: độ chính xác, thời gian, "
             "token mỗi câu hỏi vàng", f"updated: {d}", "tags: [eval]", "---", "", f"# Eval {d} (model {model})", "",
             "| Bộ | câu | hit | đúng | trả lời được | giây TB | token TB |", "|---|---|---|---|---|---|---|"]
    for name in sorted({r["set"] for r in rows}) + ["tất cả"]:
        rs = [r for r in rows if name == "tất cả" or r["set"] == name]
        dur = [r["duration_s"] for r in rs if r.get("duration_s") is not None]
        tok = [r["tokens"] for r in rs if r.get("tokens")]
        lines.append(f"| {name} | {len(rs)} | {pct([r['hit'] for r in rs])} | {pct([r['correct'] for r in rs])} | "
                     f"{pct([r['answered'] for r in rs])} | {sum(dur) / len(dur) if dur else 0:.1f} | "
                     f"{int(sum(tok) / len(tok)) if tok else '-'} |")
    lines += ["", "## Câu sai"]
    bad = [r for r in rows if not r["hit"] or r["correct"] is False]
    lines += [f"- [{r['set']}/{r.get('kind', '-')}] {r['q'][:120]} — thiếu {', '.join(r.get('expected_pages') or []) or '(bẫy)'}"
              f"; trích: {', '.join(r.get('cited') or []) or '-'}" for r in bad] or ["- Không có."]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 3.3 hub người/dự án/hệ thống
HUB_DIR = "50-knowledge/hubs"
HUB_KINDS = {"person": "người", "project": "dự án", "system": "hệ thống"}
_AUTO_START, _AUTO_END = "<!-- backlinks:auto -->", "<!-- /backlinks:auto -->"


def hub_new(base, kind, name, now=None):
    """Tạo 50-knowledge/hubs/hub-<loại>-<slug>.md từ mẫu. Trả đường dẫn tương đối (đã có thì báo lỗi)."""
    if kind not in HUB_KINDS:
        raise ValueError(f"loại hub phải là một trong {', '.join(HUB_KINDS)}")
    p = Path(base) / HUB_DIR / f"hub-{kind}-{slugify(name, 50)}.md"
    if p.exists():
        raise ValueError(f"hub đã có: {rel(base, p)}")
    d = (now or today()).isoformat()
    note = ("Chỉ ghi vai trò/phần việc, không thông tin cá nhân (AGENTS.md mục 30-people)." if kind == "person"
            else "Tóm tắt ngắn; chi tiết để ở file riêng, link về đây bằng `related: [" + p.stem + "]`.")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join([
        "---", "type: hub", f"hub_kind: {kind}", f"entity: {name}", f"title: {name}",
        f"description: Trang trung tâm {HUB_KINDS[kind]} {name}: mọi file liên quan link về đây", f"updated: {d}",
        f"tags: [hub, {kind}]", "related: []", "---", "", f"# {name}", "", note, "", "## Tóm tắt",
        "Không có trong brain", "", "## Xem thêm", _AUTO_START, _AUTO_END, ""]), encoding="utf-8")
    return rel(base, p)


def hub_backlinks(base):
    """{hub path: [(file, description)]} các file có `related` trỏ tới hub."""
    base = Path(base)
    hubs = {p.stem: rel(base, p) for p in (base / HUB_DIR).glob("*.md")}
    out = {h: [] for h in hubs.values()}
    if not hubs:
        return out
    for p in vault_files(base, FACT_DIRS):
        r = rel(base, p)
        f, _, _ = frontmatter(read(p))
        for t in fm_list(f.get("related")):
            stem = t.split("/")[-1].removesuffix(".md")
            if stem in hubs and hubs[stem] != r:
                out[hubs[stem]].append((r, f.get("description", "")))
    return out


def _auto_block(items):
    return "\n".join([_AUTO_START] + [f"- [[{Path(r).stem}]] — {d[:120]}".rstrip(" —") for r, d in sorted(items)]
                     + [_AUTO_END])


def hub_sync(base, apply=False):
    """Viết lại khối backlinks tự động trong `## Xem thêm` của mỗi hub. Trả danh sách hub đã đổi."""
    changed = []
    for h, items in hub_backlinks(base).items():
        p = Path(base) / h
        t = read(p)
        block = _auto_block(items)
        if _AUTO_START in t and _AUTO_END in t:
            new = re.sub(re.escape(_AUTO_START) + r".*?" + re.escape(_AUTO_END), lambda m: block, t, flags=re.S)
        else:
            new = t.rstrip("\n") + ("\n\n## Xem thêm\n" if "## Xem thêm" not in t else "\n") + block + "\n"
        if new != t:
            changed.append(h)
            if apply:
                p.write_text(new, encoding="utf-8")
    return changed


def hub_issues(base):
    return [{"kind": "hub-backlink", "path": h, "msg": "thiếu backlink trong Xem thêm (brain.py hub sync)",
             "block": False} for h in hub_sync(base)]
