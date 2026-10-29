"""migrate: chuyển brain second-brain-lite / thư mục markdown sang cấu trúc này."""
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from . import textsafe, upgrade, util

# ---------------------------------------------------------------- migrate
# Chuyển dữ liệu từ một second brain cấu trúc khác sang brain này. Nhận biết second-brain-lite (memory/ 1 file/fact,
# PARA 0-inbox..4-archive); thư mục markdown khác (vd vault Obsidian) thì mọi file .md vào 00-inbox/local/ cho ingest.
# Brain nguồn chỉ đọc. Mặc định chạy thử; --apply mới ghi, không ghi đè file có sẵn. Mỗi file chuyển có
# `migrated_from: <brain>:<path>` nên chạy lại không nhân bản. private/, logs/, scripts/ của nguồn không đọc.
MIGRATE_SKIP_DIRS = {".git", ".brain-jobs", "private", "logs", "scripts", ".claude", "node_modules", "__pycache__",
                     ".obsidian", ".trash", "raw"}
MIGRATE_LITE_DERIVED = ("de-xuat-", "tong-ket-tuan-", "goi-y-skill")  # đề xuất job lite tự sinh, nguồn gốc đã chuyển

def _is_lite_brain(d):
    d = Path(d)
    return ((d / "memory").is_dir() and (d / "AGENTS.md").exists()
            and ((d / ".brain-version").exists() or (d / "memory" / "MEMORY.md").exists()))

def brain_kind(d):
    """'hibrain' (cấu trúc này), 'lite' (second-brain-lite), 'other' (thư mục có .md), None (không có .md)."""
    d = Path(d)
    if upgrade._is_brain(d) and (d / "20-projects").is_dir():
        return "hibrain"
    if _is_lite_brain(d):
        return "lite"
    return "other" if any(True for _ in _migrate_md(d)) else None

def _migrate_md(src):
    for p in sorted(Path(src).rglob("*.md")):
        if not set(p.relative_to(src).parts[:-1]) & MIGRATE_SKIP_DIRS:
            yield p

def _slug(text):
    t = unicodedata.normalize("NFKD", str(text).replace("đ", "d").replace("Đ", "D"))
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60].strip("-") or "note"

def _lite_fm(text):
    """Frontmatter kiểu lite: `key: value` + 1 cấp lồng (metadata: / type:). Trả (dict, thân)."""
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return {}, text
    head, sep, body = text[4:].partition("\n---")
    if not sep:
        return {}, text
    data, parent = {}, None
    for line in head.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, _, val = line.strip().partition(":")
        key, val = key.strip(), val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if line[:1] in " \t" and parent:
            data[parent][key] = val
        elif not val:
            data[key], parent = {}, key
        else:
            data[key], parent = val, None
    return {k: ("" if v == {} else v) for k, v in data.items()}, body.lstrip("-").lstrip("\n")

def _md_sections(body):
    """{'': phần trước mục ## đầu (bỏ tiêu đề #), '<tiêu đề>': nội dung}."""
    out, cur = {"": []}, ""
    for line in body.split("\n"):
        m = re.match(r"^## +(.+?)\s*$", line)
        if m:
            cur = m.group(1)
            out.setdefault(cur, [])
        elif not (cur == "" and re.match(r"^# ", line)):
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}

def _h1(body, default):
    m = re.search(r"(?m)^# +(.+?)\s*$", body)
    return m.group(1) if m else default

def _empty(text):
    t = (text or "").strip()
    return "Không có trong brain" if not t or t.lower() in ("không có", "(chưa có)", "-") else t

def _fm_block(pairs):
    lines = ["---"]
    for k, v in pairs:
        if v not in (None, ""):
            v = " ".join(str(v).split())
            lines.append(f"{k}: {v}")
    return "\n".join(lines) + "\n---\n"

def _index_insert(text, heading, lines):
    """Chèn dòng vào cuối mục `## heading` của INDEX.md (chưa có mục thì thêm cuối file)."""
    rows = text.rstrip("\n").split("\n")
    try:
        i = rows.index(f"## {heading}")
    except ValueError:
        return "\n".join(rows + ["", f"## {heading}", *lines]) + "\n"
    j = i + 1
    while j < len(rows) and not rows[j].startswith("## "):
        j += 1
    while j > i + 1 and not rows[j - 1].strip():
        j -= 1
    return "\n".join(rows[:j] + lines + rows[j:]) + "\n"

def migrate_plan(src, target):
    """Kế hoạch chuyển: (items, edits). items: {st, src, dst, text, desc}; edits: {path: [(st, mô tả, hàm sửa)]}."""
    src, target = Path(src).expanduser().resolve(), Path(target).expanduser().resolve()
    if not upgrade._is_brain(target):
        sys.exit(f"!! {target} không phải brain đích (thiếu scripts/brain.py, AGENTS.md hoặc INDEX.md)")
    if src == target or target in src.parents or src in target.parents:
        sys.exit("!! nguồn và đích phải là hai thư mục tách riêng")
    kind = brain_kind(src)
    if kind is None:
        sys.exit(f"!! {src} không có file .md nào để chuyển")
    if kind == "hibrain":
        sys.exit("!! nguồn cùng cấu trúc với brain này: gộp bằng git (remote/merge) hoặc `upgrade`, không cần migrate")
    name, tag, today = src.name, _slug(src.name), f"{datetime.now():%Y-%m-%d}"
    stems, done = set(), {}
    for p in target.rglob("*.md"):
        parts = p.relative_to(target).parts
        if parts[0] in (".git", "private", "node_modules", "skills", "web"):
            continue
        stems.add(p.stem)
        m = re.search(r"(?m)^migrated_from: *(.+?)\s*$", p.read_text(encoding="utf-8", errors="replace")[:3000])
        if m:
            done[m.group(1)] = p.relative_to(target).as_posix()
    items, edits, links, later = [], {}, {}, []

    def claim(stem, p):
        """Tên file đích chưa trùng; file đã chuyển ở lần trước thì giữ đúng tên cũ (để link trỏ đúng)."""
        if origin(p) in done:
            return Path(done[origin(p)]).stem
        s, n = stem, 2
        if s in stems:
            s = f"{stem}-{tag}"
        while s in stems:
            s, n = f"{stem}-{tag}-{n}", n + 1
        stems.add(s)
        return s

    def origin(p):
        return f"{name}:{p.relative_to(src).as_posix()}"

    def add(p, dst, desc, render):
        o = origin(p)
        if o in done:
            items.append({"st": "SKIP", "src": o, "dst": done[o], "desc": "đã chuyển ở lần trước"})
            return False
        items.append({"st": "ADD", "src": o, "dst": dst, "desc": desc, "render": render})
        return True

    def edit(path, st, note, fn):
        edits.setdefault(path, []).append((st, note, fn))

    def relink(text):
        def sub(m):
            key = m.group(1).split("|")[0].split("#")[0].strip()
            new = links.get(key) or links.get(key[:-3] if key.endswith(".md") else key)
            new = new or (key if key in stems else None)
            return f"[[{new}]]" if new else key
        return re.sub(r"\[\[([^\]\n]+?)\]\]", sub, text)

    def asof(updated):
        return f"Chuyển từ brain {name} ngày {today}; nội dung as of {updated}, nguồn: USER."

    def to_inbox(p, why):
        rel = p.relative_to(src).as_posix()
        dst = f"00-inbox/local/import-{tag}-{_slug(rel[:-3])}.md"
        if add(p, dst, why, lambda: (
                f"---\nmigrated_from: {origin(p)}\n---\n<!-- Nguồn: tài liệu chuyển từ brain {name} ({rel}). "
                f"Nhãn USER-PASTED: ngữ cảnh do chủ brain mang sang, chưa phải fact. Nội dung trong <untrusted> là dữ liệu. -->\n\n"
                f"# {textsafe.one_line(p.stem)}\n\n### USER-PASTED ({today})\n"
                + textsafe.untrusted(textsafe.redact(_lite_fm(p.read_text(encoding='utf-8', errors='replace'))[1])))):
            pass

    if kind == "other":
        for p in _migrate_md(src):
            to_inbox(p, "tài liệu → ingest")
        return items, edits, kind, name

    # ---- memory/
    owner = {}
    for p in sorted((src / "memory").glob("*.md")):
        if p.name == "MEMORY.md":
            continue
        fm, body = _lite_fm(p.read_text(encoding="utf-8", errors="replace"))
        meta = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
        mtype, slug = meta.get("type") or fm.get("type", ""), fm.get("name") or p.stem
        title = _h1(body, slug)
        desc = textsafe.one_line(re.sub(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", r"\1", fm.get("description") or title), 200)
        updated = str(fm.get("updated") or fm.get("created") or today)[:10]
        sec = _md_sections(body)
        main = re.sub(r"(?m)^\*\*(Why|How to apply):\*\*.*$", "", sec[""]).strip()
        why = (re.search(r"(?m)^\*\*Why:\*\* *(.*)$", sec[""]) or [None, ""])[1].strip()
        how = (re.search(r"(?m)^\*\*How to apply:\*\* *(.*)$", sec[""]) or [None, ""])[1].strip()
        if slug in ("nguoi-dung", "uu-tien-hien-tai"):
            links[slug] = "CRITICAL"
            if slug == "nguoi-dung":
                for key, label in (("name", "Tên"), ("role", "Vai trò")):
                    m = re.search(rf"(?m)^- {label}: *(.+)$", body)
                    if m:
                        owner[key] = m.group(1).strip()
            else:
                pr = re.findall(r"(?m)^(?:\d+\.|-) +(.+)$", main)
                if pr:
                    owner["priorities"] = "; ".join(x.strip() for x in pr)
            continue
        if mtype == "reference" and slug.startswith("nguoi-"):
            links[slug] = "team-map"
            later.append(("team", p, title, desc, main))
            continue
        if mtype == "feedback":
            stem = claim("rule-" + _slug(slug), p)
            links[slug] = stem
            ack = "false" if fm.get("ack") == "no" else "true"
            applies = fm.get("applies_to", "")
            ev = [l for l in sec.get("Bằng chứng", "").split("\n") if l.strip().startswith("- ")]

            def render(p=p, title=title, desc=desc, updated=updated, main=main, why=why, how=how, ack=ack,
                       applies=applies, ev=ev):
                evl = []
                for line in ev:
                    m = re.match(r'^- (\S+ \S+) · (.*?) · (.*?) · "(.*)"$', line.strip())
                    evl.append(f'- "{m.group(4)}" — brain {name} {p.relative_to(src).as_posix()}, {m.group(1)[:10]} '
                               f'({m.group(2)}, {m.group(3)})' if m else line.strip())
                evl = evl or [f'- "{desc}" — brain {name} {p.relative_to(src).as_posix()}, {updated} '
                              "(brain cũ không ghi câu nguyên văn)"]
                apply_txt = (how or "(chưa ghi, chờ chủ brain bổ sung)").rstrip(".") + "." + (
                    f" Chỉ áp dụng trong dự án {applies}; dự án khác KHÔNG áp dụng." if applies else "")
                return (_fm_block([("type", "rule"), ("title", title), ("description", desc), ("updated", updated),
                                   ("last_verified", updated), ("tags", "[rule, migrated]"), ("confidence", "0.9"),
                                   ("source", f"USER (brain {name})"), ("ack", ack), ("applies_to", applies),
                                   ("migrated_from", origin(p)), ("related", "[[working-preferences]]")])
                        + f"**Luật:** {textsafe.redact(relink(main or desc))}\n\n"
                        f"**Why:** {textsafe.redact(why) or '(suy luận, chờ xác nhận)'}\n\n"
                        f"**How to apply:** {textsafe.redact(apply_txt)}\n\n**Bằng chứng:**\n" + "\n".join(map(textsafe.redact, evl)) + "\n")
            dst = f"50-knowledge/rules/{stem}.md"
            if add(p, dst, desc, render):
                edit("50-knowledge/working-preferences.md", "APPEND", f"index luật [[{stem}]]",
                     lambda t, stem=stem, desc=desc, how=how: _index_insert(
                         t, "Luật làm việc", [f"- [[{stem}]] — {desc} — khi: {textsafe.one_line(how or 'xem file luật', 100)}"]))
            continue
        if mtype in ("user", "project", "reference"):
            top = "90-reference" if mtype == "reference" else "50-knowledge"
            stem = claim(_slug(slug), p)
            links[slug] = stem
            extra = "\n\n".join(f"## {h}\n{v}" for h, v in sec.items() if h and v)

            def render(p=p, title=title, desc=desc, updated=updated, main=main, why=why, how=how, extra=extra,
                       mtype=mtype):
                wh = (f"\n\n**Why:** {why}\n**How to apply:** {how}" if why or how else "")
                return (_fm_block([("type", "reference" if mtype == "reference" else "knowledge"), ("title", title),
                                   ("description", desc), ("updated", updated), ("last_verified", updated),
                                   ("tags", f"[{ {'user': 'owner', 'project': 'context'}.get(mtype, 'reference')}, migrated]"),
                                   ("confidence", "0.9"), ("migrated_from", origin(p)),
                                   ("related", "[[working-preferences]]" if mtype == "user" else "[]")])
                        + f"# {title}\n\n- {asof(updated)}\n\n{textsafe.redact(relink(main or desc))}{textsafe.redact(wh)}\n"
                        + (f"\n{textsafe.redact(relink(extra))}\n" if extra else ""))
            add(p, f"{top}/{stem}.md", desc, render)
            continue
        to_inbox(p, f"memory loại '{mtype or '?'}' không nhận ra → ingest")

    # ---- dự án: 1-projects/<x>/_dashboard.md, 4-archive/<x>/_dashboard.md (done)
    areas_used = {}
    for base, forced in (("1-projects", None), ("4-archive", "done")):
        for dash in sorted((src / base).glob("*/_dashboard.md")):
            d = dash.parent
            fm, body = _lite_fm(dash.read_text(encoding="utf-8", errors="replace"))
            title = fm.get("title") or _h1(body, d.name)
            stem = claim(_slug(d.name), dash)
            links[d.name] = stem
            area = "area-" + _slug(fm["area"]) if fm.get("area") else "area-general"
            areas_used.setdefault(area, []).append(stem)
            status = forced or (fm.get("status") if fm.get("status") in ("active", "idle", "done") else "active")
            updated = str(fm.get("updated") or today)[:10]
            sec = _md_sections(body)
            notes = []
            for f in sorted(d.rglob("*")):
                if f == dash or not f.is_file() or set(f.relative_to(d).parts) & MIGRATE_SKIP_DIRS:
                    continue
                if f.suffix != ".md":
                    items.append({"st": "MANUAL", "src": origin(f), "dst": "", "desc": "file không phải .md: chép tay nếu cần"})
                    continue
                nstem = claim(f"{stem}-{_slug(f.relative_to(d).as_posix()[:-3])}", f)
                notes.append(nstem)
                links[f.stem] = nstem

                def render_note(f=f, nstem=nstem, title=title, stem=stem):
                    nfm, nbody = _lite_fm(f.read_text(encoding="utf-8", errors="replace"))
                    up = str(nfm.get("updated") or updated)[:10]
                    return (_fm_block([("type", "knowledge"), ("title", f"{title}: {nfm.get('title') or _h1(nbody, f.stem)}"),
                                       ("description", f"Ghi chú dự án {title} ({f.name}) từ brain {name}"),
                                       ("updated", up), ("tags", "[project-note, migrated]"), ("confidence", "0.8"),
                                       ("migrated_from", origin(f)), ("related", f"[[{stem}]]")])
                            + f"- {asof(up)}\n\n{textsafe.redact(relink(nbody.strip()))}\n")
                add(f, f"50-knowledge/{nstem}.md", f"ghi chú dự án {title}", render_note)

            def render_dash(dash=dash, title=title, stem=stem, area=area, status=status, updated=updated, sec=sec,
                            fm=fm, notes=notes):
                std = ("Trạng thái", "Đang treo", "Next steps", "Quyết định", "Xem thêm")
                state = _empty(sec.get("Trạng thái"))
                desc = textsafe.one_line(f"Dự án {title}: " + (state if state != "Không có trong brain" else status), 200)
                more = [x for x in [sec.get("Xem thêm", "")] if _empty(x) != "Không có trong brain"]
                more += [f"- [[{n}]]" for n in notes]
                more += [f"### {h}\n{v}" for h, v in sec.items() if h and h not in std and v]
                if sec.get(""):
                    more.append(sec[""])
                body = "\n\n".join([
                    f"## Trạng thái\n- {asof(updated)}\n{state if state != 'Không có trong brain' else ''}".rstrip(),
                    f"## Đang treo\n{_empty(sec.get('Đang treo'))}", f"## Next steps\n{_empty(sec.get('Next steps'))}",
                    f"## Quyết định\n{_empty(sec.get('Quyết định'))}",
                    "## Xem thêm\n" + ("\n".join(more) if more else "Không có trong brain")])
                return (_fm_block([("type", "project"), ("title", title), ("description", desc), ("updated", updated),
                                   ("last_verified", updated), ("status", status), ("area", area),
                                   ("repo", fm.get("repo") or "none"), ("last_activity", f"{updated} (brain {name})"),
                                   ("due", fm.get("due")), ("tags", "[project, migrated]"), ("confidence", "0.8"),
                                   ("migrated_from", origin(dash)), ("related", f"[[{area}]]")])
                        + textsafe.redact(relink(body)) + "\n")
            add(dash, f"20-projects/{stem}.md", f"dự án {title} ({status})", render_dash)

    # ---- 2-areas/
    for p in sorted((src / "2-areas").glob("*.md")):
        if p.name.lower() == "readme.md":
            continue
        fm, body = _lite_fm(p.read_text(encoding="utf-8", errors="replace"))
        stem = "area-" + _slug(p.stem)
        links[p.stem] = stem
        title = fm.get("title") or _h1(body, p.stem)
        if (target / "25-areas" / f"{stem}.md").exists():
            items.append({"st": "SKIP", "src": origin(p), "dst": f"25-areas/{stem}.md", "desc": "đích đã có area này"})
            areas_used.pop(stem, None)
            continue
        projs = areas_used.pop(stem, [])

        def render_area(p=p, title=title, fm=fm, body=body, projs=projs):
            sec = _md_sections(body)
            updated = str(fm.get("updated") or today)[:10]
            scope = "\n".join(x for x in (sec.get(""), sec.get("Ghi chú")) if _empty(x) != "Không có trong brain")
            more = [f"### {h}\n{v}" for h, v in sec.items() if h and h not in ("Ghi chú", "Mục tiêu / tiêu chuẩn") and v]
            return (_fm_block([("type", "area"), ("title", title), ("description", textsafe.one_line(f"Mảng {title}: " + (scope or "chuyển từ brain " + name), 200)),
                               ("updated", updated), ("tags", "[area, migrated]"), ("confidence", "1.0"),
                               ("migrated_from", origin(p)), ("related", ", ".join(f"[[{x}]]" for x in projs) or "[]")])
                    + textsafe.redact(relink(f"## Phạm vi\n- {asof(updated)}\n{scope}".rstrip() + "\n\n"
                                    f"## Tiêu chuẩn cần giữ\n{_empty(sec.get('Mục tiêu / tiêu chuẩn'))}\n\n"
                                    "## Dự án\n" + ("\n".join(f"- [[{x}]]" for x in projs) or "Không có trong brain")
                                    + "\n\n## Xem thêm\n" + ("\n\n".join(more) or "Không có trong brain"))) + "\n")
        add(p, f"25-areas/{stem}.md", f"mảng {title}", render_area)
    for stem, projs in sorted(areas_used.items()):  # dự án trỏ tới area chưa có file (vd area-general)
        if (target / "25-areas" / f"{stem}.md").exists() or any(i["dst"] == f"25-areas/{stem}.md" for i in items):
            continue
        title = stem[5:].replace("-", " ").capitalize()
        items.append({"st": "ADD", "src": f"{name}:(tạo cho dự án)", "dst": f"25-areas/{stem}.md", "desc": f"mảng {title}",
                      "render": lambda stem=stem, title=title, projs=projs: (
                          _fm_block([("type", "area"), ("title", title),
                                     ("description", f"Mảng {title} (tạo khi chuyển từ brain {name}, chờ chủ brain mô tả)"),
                                     ("updated", today), ("tags", "[area, migrated]"), ("confidence", "0.5"),
                                     ("related", ", ".join(f"[[{x}]]" for x in projs))])
                          + "## Phạm vi\nKhông có trong brain\n\n## Tiêu chuẩn cần giữ\nKhông có trong brain\n\n## Dự án\n"
                          + "\n".join(f"- [[{x}]]" for x in projs) + "\n\n## Xem thêm\nKhông có trong brain\n")})

    # ---- 3-resources/ → 50-knowledge/
    for p in sorted((src / "3-resources").rglob("*.md")) if (src / "3-resources").is_dir() else []:
        if p.name.lower() == "readme.md":
            continue
        fm, body = _lite_fm(p.read_text(encoding="utf-8", errors="replace"))
        title = fm.get("title") or _h1(body, p.stem)
        stem = claim(_slug(p.relative_to(src / "3-resources").as_posix()[:-3]), p)
        links[p.stem] = stem
        sec = _md_sections(body)
        desc = textsafe.one_line(fm.get("description") or (title + ": " + _empty(sec.get("Tóm tắt")).split("\n")[0]), 200)

        def render_res(p=p, title=title, fm=fm, body=body, desc=desc):
            updated = str(fm.get("updated") or today)[:10]
            text = re.sub(r"(?m)^# .*\n?", "", body, count=1).strip()
            return (_fm_block([("type", "knowledge"), ("title", title), ("description", desc), ("updated", updated),
                               ("tags", "[resource, migrated]"), ("confidence", "0.8"), ("source_doc", fm.get("source")),
                               ("migrated_from", origin(p)), ("related", "[]")])
                    + f"# {title}\n\n- {asof(updated)}\n\n{textsafe.redact(relink(text))}\n")
        add(p, f"50-knowledge/{stem}.md", desc, render_res)

    # ---- 4-archive/ (trừ dashboard đã xử lý ở trên)
    for p in sorted((src / "4-archive").rglob("*.md")) if (src / "4-archive").is_dir() else []:
        if p.name.lower() == "readme.md" or p.name == "_dashboard.md" or (p.parent / "_dashboard.md").exists():
            continue
        rejected = "luat-da-bo" in p.relative_to(src).parts
        stem = claim(_slug(p.relative_to(src / "4-archive").as_posix()[:-3]), p)

        def render_arch(p=p, rejected=rejected):
            fm, body = _lite_fm(p.read_text(encoding="utf-8", errors="replace"))
            title = fm.get("title") or _h1(body, p.stem)
            return (_fm_block([("type", "rule" if rejected else "archive"), ("title", title),
                               ("description", ("Luật chủ brain đã bỏ ở brain cũ, không tạo lại" if rejected
                                                else f"Lưu trữ từ brain {name}")),
                               ("updated", today), ("invalid_at", today if rejected else ""),
                               ("migrated_from", origin(p))]) + textsafe.redact(body.strip()) + "\n")
        add(p, f"archive/{stem}.md", "luật đã bỏ" if rejected else "lưu trữ", render_arch)

    # ---- 0-inbox/
    for p in sorted((src / "0-inbox").glob("*.md")) if (src / "0-inbox").is_dir() else []:
        if p.name.lower() == "readme.md":
            continue
        if p.name.startswith(MIGRATE_LITE_DERIVED):
            items.append({"st": "SKIP", "src": origin(p), "dst": "", "desc": "đề xuất job lite tự sinh, không chuyển"})
            continue
        if p.name.startswith("luat-"):
            o = origin(p)
            if o in done or any(o in l for l in (target / "eval" / "review-queue.md").read_text(
                    encoding="utf-8").splitlines() if (target / "eval" / "review-queue.md").exists()):
                items.append({"st": "SKIP", "src": o, "dst": "eval/review-queue.md", "desc": "đã chuyển ở lần trước"})
                continue
            fm, body = _lite_fm(p.read_text(encoding="utf-8", errors="replace"))
            q = re.findall(r'(?m)^- \S+ \S+ · .*? · .*? · "(.*)"$', body)
            line = (f"- [ ] luật ứng viên (brain {name}): {textsafe.one_line(_h1(body, p.stem), 120)} — "
                    f"bằng chứng: {'; '.join(chr(34) + x[:120] + chr(34) for x in q[:3]) or 'không có'} — nguồn: {o}")
            edit("eval/review-queue.md", "APPEND", f"luật ứng viên {p.name}",
                 lambda t, line=textsafe.redact(line): t.rstrip("\n") + "\n" + line + "\n")
            continue
        to_inbox(p, "tài liệu trong inbox → ingest")

    # ---- file .md ngoài cấu trúc lite (thư mục người dùng tự thêm) → ingest
    known = {"memory", "0-inbox", "1-projects", "2-areas", "3-resources", "4-archive"}
    for p in _migrate_md(src):
        parts = p.relative_to(src).parts
        if parts[0] in known or (len(parts) == 1 and p.name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md")):
            continue
        to_inbox(p, "file ngoài cấu trúc lite → ingest")

    # ---- người khác → 30-people/team-map.md; chủ brain + ưu tiên → CRITICAL.md
    for _, p, title, desc, main in later:
        o = origin(p)
        line = textsafe.redact(f"- {title}: {textsafe.one_line(main or desc, 300)} (as of {today}, nguồn: USER, brain {o})")
        if o in done or (target / "30-people" / "team-map.md").exists() and o in (
                target / "30-people" / "team-map.md").read_text(encoding="utf-8"):
            items.append({"st": "SKIP", "src": o, "dst": "30-people/team-map.md", "desc": "đã chuyển ở lần trước"})
            continue
        edit("30-people/team-map.md", "APPEND", f"người: {title}",
             lambda t, line=line: (t or _fm_block([("type", "people"), ("title", "Team map"),
                                                   ("description", "Ai giữ việc gì (chỉ vai trò, không thông tin cá nhân)"),
                                                   ("updated", today), ("tags", "[people]"), ("confidence", "0.9"),
                                                   ("related", "[]")]) + "# Team map\n").rstrip("\n") + "\n" + line + "\n")
    if owner:
        crit = (target / "CRITICAL.md").read_text(encoding="utf-8") if (target / "CRITICAL.md").exists() else ""

        def fill(t):
            out = []
            for l in t.split("\n"):
                if l.startswith("- Chủ brain:") and "(chưa điền)" in l and owner.get("name"):
                    l = f"- Chủ brain: {owner['name']}. Vai trò: {owner.get('role', '(chưa điền)')}"
                elif l.startswith("- Ưu tiên") and "(chưa điền)" in l and owner.get("priorities"):
                    l = f"- Ưu tiên hiện tại: {owner['priorities']}"
                out.append(l)
            return "\n".join(out)
        if fill(crit) != crit:
            edit("CRITICAL.md", "APPEND", "điền chủ brain / ưu tiên từ brain cũ", fill)
        elif not all(v in crit for v in owner.values()):
            items.append({"st": "MANUAL", "src": f"{name}:memory/nguoi-dung.md, uu-tien-hien-tai.md", "dst": "CRITICAL.md",
                          "desc": "CRITICAL.md đã có nội dung, gộp tay nếu khác: " + "; ".join(f"{k}={v}" for k, v in owner.items())})
    if (src / "private").is_dir():
        items.append({"st": "NOTE", "src": f"{name}:private/", "dst": "", "desc": "không đọc, không chuyển; tự chép tay nếu cần"})
    return items, edits, kind, name

def cmd_migrate(src, target, apply=False):
    target = Path(target).expanduser().resolve()
    items, edits, kind, name = migrate_plan(src, target)
    today = f"{datetime.now():%Y-%m-%d}"
    added = [i for i in items if i["st"] == "ADD"]
    idx_lines = {}
    for i in added:
        text = i["render"]()
        top = i["dst"].split("/")[0]
        if top in ("20-projects", "25-areas", "30-people", "40-decisions", "50-knowledge", "90-reference"):
            m = re.search(r"(?m)^description: *(.+)$", text)
            u = re.search(r"(?m)^updated: *(.+)$", text)
            idx_lines.setdefault(top, []).append(f"- `{i['dst']}` — {m.group(1) if m else i['desc']} — {u.group(1) if u else today}")
        if apply:
            dst = target / i["dst"]
            if dst.exists():
                i["st"], i["desc"] = "SKIP", "đích đã có file, không ghi đè"
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(text, encoding="utf-8")
    if "30-people/team-map.md" in edits and not (target / "30-people" / "team-map.md").exists():
        idx_lines.setdefault("30-people", []).append(
            "- `30-people/team-map.md` — Ai giữ việc gì (chỉ vai trò, không thông tin cá nhân) — " + today)
    n_written = sum(1 for i in added if i["st"] == "ADD")
    if idx_lines:
        def add_index(t):
            for h, ls in idx_lines.items():
                t = _index_insert(t, h, ls)
            return t
        edits.setdefault("INDEX.md", []).append(("APPEND", f"{sum(map(len, idx_lines.values()))} dòng chỉ mục", add_index))
    if n_written or any(k != "INDEX.md" for k in edits):
        edits.setdefault("LOG.md", []).append(("APPEND", "1 dòng nhật ký", lambda t: t.rstrip("\n") +
                                               f"\n- {today} migrate: {n_written} file từ brain {name} ({kind}) (USER)\n"))
    for path, fns in edits.items():
        for st, note, _ in fns:
            print(f"{st:7} {path:46} {note}")
        if apply:
            p = target / path
            text = p.read_text(encoding="utf-8") if p.exists() else ""
            for _, _, fn in fns:
                text = fn(text)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
    for i in items:
        print(f"{i['st']:7} {i['dst'] or '-':46} ← {i['src']}  {i['desc']}")
    n = {k: sum(1 for i in items if i["st"] == k) for k in ("ADD", "SKIP", "MANUAL", "NOTE")}
    inbox = sum(1 for i in added if i["dst"].startswith("00-inbox/") and i["st"] == "ADD")
    print(f"\nnguồn: {name} ({kind}). {n['ADD']} ADD, {n['SKIP']} SKIP, {n['MANUAL']} MANUAL, {n['NOTE']} NOTE; "
          f"{inbox} file vào 00-inbox/local/ chờ ingest"
          + ("" if apply else "  (dry-run: thêm --apply để ghi)"))
    if apply:
        util.log(f"migrate {name} ({kind}) -> {n_written} file, {inbox} inbox")
        print("Tiếp: `brain.py check`, rồi `brain.py run ingest` cho file inbox (mỗi lượt 5 file).")
    return 0
