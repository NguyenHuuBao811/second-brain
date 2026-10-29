"""learn: chủ đề, chống trùng, rào sửa file, đề xuất, digest."""
import difflib
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from . import config, dispatching, learnfeed, learnpending, textsafe, util

def learn_topics():
    """[(nhóm, chủ đề)] từ 50-knowledge/learn-topics.md (chủ brain sửa): mỗi dòng `- ` dưới một mục `## ` là một
    chủ đề. Không có file / không có dòng nào thì dùng danh sách mặc định."""
    p = config.BASE / learnfeed.LEARN_TOPICS
    _, body = dispatching._frontmatter(p.read_text(encoding="utf-8", errors="replace") if p.exists() else "")
    group, out = "", []
    for line in body.splitlines():
        if line.startswith("## "):
            group = line[3:].strip()
        elif group and re.match(r"^[-*] \S", line):
            out.append((group, line[2:].strip()))
    return out or learnfeed.LEARN_DEFAULT_TOPICS

def learn_pick_topic(topics, st, context):
    """Chủ đề web lượt này: xoay vòng từ st["topic_i"], ưu tiên chủ đề có từ khoá xuất hiện trong việc hôm nay,
    không lặp chủ đề vừa học ở vài lượt trước. Trả ((nhóm, chủ đề), [2 chủ đề dự phòng]); cập nhật st."""
    n = len(topics)
    words = set(re.findall(r"\w{4,}", context.lower())) - learnfeed._TOPIC_STOP
    recent = st.get("recent_topics") or []
    start = int(st.get("topic_i") or 0) % n
    order = [(start + k) % n for k in range(n)]
    related = [i for i in order if topics[i][1] not in recent
               and words & (set(re.findall(r"\w{4,}", topics[i][1].lower())) - learnfeed._TOPIC_STOP)]
    i = related[0] if related else next((i for i in order if topics[i][1] not in recent), start)
    st["topic_i"] = (i + 1) % n
    st["recent_topics"] = (recent + [topics[i][1]])[-min(3, n - 1):] if n > 1 else []
    return topics[i], [topics[(i + k) % n] for k in (1, 2) if k < n]

def learned_files():
    return sorted((config.BASE / "50-knowledge").glob("learned-*.md"))

def learned_today():
    """Số file learned-* mới hôm nay: đã commit từ nửa đêm + chưa commit + mục chờ duyệt tạo hôm nay."""
    spec = "50-knowledge/learned-*.md"
    added = util.git("log", "--since=midnight", "--diff-filter=A", "--name-only", "--format=", "--", spec).stdout.split()
    # learned mới giờ nằm chờ duyệt ở 00-inbox/learn-pending/ (USER 2026-10-28): tính cả mục chờ tạo hôm nay
    return (len(set(added) | set(util.git("ls-files", "--others", "--exclude-standard", "--", spec).stdout.split()))
            + learnpending.created_today())

def _norm_words(s):
    s = unicodedata.normalize("NFKD", str(s).lower().replace("đ", "d"))
    return " ".join(re.findall(r"[a-z0-9]+", "".join(ch for ch in s if not unicodedata.combining(ch))))

def _dupe_key(name, title):
    return _norm_words(Path(name).stem.removeprefix("learned-").replace("-", " ")), _norm_words(title)

def _same_topic(a, b):
    return (difflib.SequenceMatcher(None, a[0], b[0]).ratio() >= 0.85
            or bool(a[1] and b[1] and difflib.SequenceMatcher(None, a[1], b[1]).ratio() >= 0.8))

def learned_dupe(path, existing, pending=None):
    """File learned cũ (hoặc tên file đích của mục đang chờ duyệt, `pending` {tên: tiêu đề}) cùng chủ đề với `path`
    (slug hoặc tiêu đề gần như trùng), không có thì None."""
    def key(p):
        fm, _ = dispatching._frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        return _dupe_key(p.name, fm.get("title", ""))
    me = key(path)
    for e in existing:
        if e != path and _same_topic(me, key(e)):
            return e
    for name, title in (pending or {}).items():
        if name != path.name and _same_topic(me, _dupe_key(name, title)):
            return Path(name)
    return None

def _index_drop(rel):
    idx = config.BASE / "INDEX.md"
    if idx.exists():
        lines = idx.read_text(encoding="utf-8").splitlines(keepends=True)
        idx.write_text("".join(l for l in lines if f"`{rel}`" not in l), encoding="utf-8")

def learn_guard(before, cap_left, pending=None):
    """Sau lượt learn: file learned-* mới mà trùng file cũ / mục đang chờ duyệt hoặc vượt trần ngày thì xoá (file do
    chính lượt này tạo, chưa commit) cùng dòng INDEX của nó. before: tên file learned có trước lượt. pending: {tên file
    đích: tiêu đề} mục chờ duyệt; file trùng đúng tên mục chờ là cập nhật mục đó, không tính trần. Trả (giữ, [(tên, lý do)])."""
    files, pending = learned_files(), pending or {}
    kept, dropped, old, n_new = [], [], [p for p in files if p.name in before], 0
    for p in (p for p in files if p.name not in before):
        if p.name in pending:
            kept.append(p)
            continue
        dup = learned_dupe(p, old + kept, pending)
        why = (f"trùng {dup.name}" if dup else
               f"quá {learnfeed.LEARN_NEW_PER_DAY} file learned mới/ngày" if n_new >= cap_left else "")
        if not why:
            kept.append(p)
            n_new += 1
            continue
        p.unlink()
        _index_drop(p.relative_to(config.BASE).as_posix())
        dropped.append((p.name, why))
    return kept, dropped

def _data_snapshot():
    return {p.relative_to(config.BASE).as_posix(): p.stat().st_mtime_ns
            for d in config.DATA_DIRS if (config.BASE / d).exists() for p in (config.BASE / d).rglob("*.md")}

def learn_fix_index(paths):
    """File learn ghi mà INDEX.md chưa có dòng thì code tự thêm từ frontmatter (luật: mỗi file ghi có dòng INDEX)."""
    idx = config.BASE / "INDEX.md"
    if not idx.exists() or not paths:
        return []
    lines, added = idx.read_text(encoding="utf-8").splitlines(), []
    for rel in paths:
        if any(f"`{rel}`" in l for l in lines) or not (config.BASE / rel).exists():
            continue
        fm, _ = dispatching._frontmatter((config.BASE / rel).read_text(encoding="utf-8", errors="replace"))
        top = rel.split("/")[0]
        at = max((i for i, l in enumerate(lines) if l.startswith(f"- `{top}/")), default=len(lines) - 1)
        desc = textsafe.one_line(fm.get("description") or fm.get("title") or rel, 300)
        lines.insert(at + 1, f"- `{rel}` — {desc} — {fm.get('updated') or f'{datetime.now():%Y-%m-%d}'}")
        added.append(rel)
    if added:
        idx.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return added

def learn_fix_log(before, changed, dropped):
    """Lượt learn ghi file mà không thêm dòng `learn:` vào LOG.md thì code thêm; file bị bỏ cũng ghi một dòng."""
    p = config.BASE / "LOG.md"
    now_txt = p.read_text(encoding="utf-8") if p.exists() else ""
    added = now_txt[len(before):] if now_txt.startswith(before) else now_txt
    day, rows = f"{datetime.now():%Y-%m-%d}", []
    if changed and not re.search(r"(?m)^- \d{4}-\d{2}-\d{2} learn:", added):
        rows.append(f"- {day} learn: UPDATE {', '.join(changed[:8])} (dòng LOG do code ghi thay) (git)")
    rows += [f"- {day} learn: bỏ 50-knowledge/{name} ({why})" for name, why in dropped]
    if rows:
        p.write_text(now_txt + ("" if not now_txt or now_txt.endswith("\n") else "\n") + "\n".join(rows) + "\n",
                     encoding="utf-8")
    return rows


_PROP_RE = re.compile(r"(?m)^## (P\d+)\.\s*(.*)$")

def proposal_sections(text):
    """{P1: (tiêu đề, trạng thái, nội dung mục)} của bot-improvement-proposals.md."""
    text, out = text or "", {}
    heads = list(_PROP_RE.finditer(text))
    for k, h in enumerate(heads):
        body = text[h.end():heads[k + 1].start() if k + 1 < len(heads) else len(text)]
        m = re.search(r"(?m)^- status:\s*([^(\n]*)", body)
        out[h.group(1)] = (h.group(2).strip(), m.group(1).strip() if m else "", body.strip())
    return out

def proposal_changes(before, after):
    """So file đề xuất trước/sau lượt learn. new: mục mới; status: đổi trạng thái (hai loại này DM ngay);
    evidence: cùng trạng thái, chỉ thêm bằng chứng/sửa chữ (không DM, gộp tóm tắt 18:00)."""
    b, ch = proposal_sections(before), {"new": [], "status": [], "evidence": []}
    for pid, (title, status, body) in proposal_sections(after).items():
        if pid not in b:
            ch["new"].append((pid, title, status))
        elif status != b[pid][1]:
            ch["status"].append((pid, title, b[pid][1], status))
        elif body != b[pid][2]:
            ch["evidence"].append((pid, title))
    return ch

def learn_digest(st, now=None):
    """Tóm tắt đề xuất cũ chỉ thêm bằng chứng: gửi 1 lần/ngày từ LEARN_DIGEST_HOUR nếu có. Trả tin ("" = chưa/không có)."""
    now = now or datetime.now()
    d = st.setdefault("digest", {"items": [], "sent": ""})
    day = f"{now:%Y-%m-%d}"
    if now.hour < learnfeed.LEARN_DIGEST_HOUR or d.get("sent") == day or not d.get("items"):
        return ""
    count = {}
    for pid, title in d["items"]:
        count.setdefault((pid, title), 0)
        count[(pid, title)] += 1
    d["items"], d["sent"] = [], day
    return ("📋 Tóm tắt hôm nay: đề xuất cũ có thêm bằng chứng (chưa đổi trạng thái)"
            + "".join(f"\n• {pid} {textsafe.one_line(t, 150)} (+{k} lần)" for (pid, t), k in count.items()))
