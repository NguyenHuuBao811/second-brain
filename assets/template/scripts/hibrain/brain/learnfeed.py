"""learn (tự học mỗi giờ): trạng thái, đọc phiên DM, lời chủ brain, đầu vào."""
import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from . import config, larkcli, larkcollect, textsafe, util

# ---------------------------------------------------------------- learn: tự học mỗi giờ (USER 2026-10-20)
# Nâng cấp 2026-10-20: đầu vào thêm phiên DM chủ brain ↔ bot và tin Lark (kéo trước mỗi lượt); mỗi lượt Claude chạy thì
# tìm web theo 50-knowledge/learn-topics.md; chỉ DM khi có mục mới, đề xuất cũ chỉ thêm bằng chứng thì gộp tóm tắt 18:00.
LEARN_MAX = 60000
LEARN_BUDGET = 2.0
LEARN_NEW_PER_DAY = 5      # file learned-*.md mới tối đa mỗi ngày
LEARN_DIGEST_HOUR = 18     # giờ gửi tóm tắt đề xuất cũ chỉ thêm bằng chứng (1 lần/ngày)
LEARN_TOPICS = "50-knowledge/learn-topics.md"
LEARN_PROPOSALS = "50-knowledge/bot-improvement-proposals.md"
# Chỉ dùng khi chưa có 50-knowledge/learn-topics.md: chủ đề chung, chủ brain thay bằng danh sách của mình.
LEARN_DEFAULT_TOPICS = [("Nghề AI engineer", "agent harness, Claude Code"),
                        ("Nghề AI engineer", "second brain, eval cho agent")]
# Từ quá chung (có trong gần như mọi đầu vào): không dùng để đoán chủ đề nào liên quan việc hôm nay.
_TOPIC_STOP = {"agent", "claude", "brain", "lark", "code", "những", "việc", "trong", "người", "được", "không", "kiếm",
               "tiền", "with", "from", "this", "that", "side"}

def learn_web_hours():
    """Không có việc mới thì cứ mỗi N giờ (LEARN_WEB_HOURS, mặc định 3) mới gọi Claude chỉ để học web."""
    try:
        return float(os.environ.get("LEARN_WEB_HOURS") or 3)
    except ValueError:
        return 3.0

def learn_last():
    """Mốc lần học trước (epoch), lần đầu: 1 giờ trước."""
    try:
        return float(((config.LOGS / "learn") / "last.txt").read_text())
    except (OSError, ValueError):
        return time.time() - 3600

def learn_mark():
    (config.LOGS / "learn").mkdir(parents=True, exist_ok=True)
    ((config.LOGS / "learn") / "last.txt").write_text(str(time.time()))

def learn_state():
    """logs/learn/state.json: offset phiên DM, lượt chủ đề, lần web cuối, cờ lỗi lark-cli, hàng tóm tắt 18:00."""
    try:
        st = json.loads(((config.LOGS / "learn") / "state.json").read_text(encoding="utf-8"))
        return st if isinstance(st, dict) else {}
    except (OSError, ValueError):
        return {}

def learn_save(st):
    (config.LOGS / "learn").mkdir(parents=True, exist_ok=True)
    ((config.LOGS / "learn") / "state.json").write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")

def _bot_log(since):
    """Dòng lỗi / im / chỉ tag của bot Lark từ `since` (systemd user journal; máy không có thì rỗng)."""
    try:
        r = subprocess.run(["journalctl", "--user", "-u", os.environ.get("BRAIN_BOT_UNIT", "hibrain-lark-bot"), "--no-pager", "-o", "cat",
                            "--since", datetime.fromtimestamp(since).strftime("%Y-%m-%d %H:%M:%S")],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return []
    keep = re.compile(r"(?i)lỗi|error|traceback|\bim\b|chỉ tag|không liên quan|hết quota|failed|từ chối")
    return [l for l in r.stdout.splitlines() if keep.search(l)][-80:]


_SID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

def learn_dm_transcripts():
    """Transcript phiên DM chủ brain ↔ bot. Bot chạy `claude -p --resume <id>` trong thư mục brain, id ở
    private/lark-bot-state/dm-session*.txt (cả bản cũ đã cất), Claude Code lưu ở ~/.claude/projects/<thư mục>/<id>.jsonl
    (tìm theo id ở mọi thư mục: id là UUID, không phụ thuộc đường dẫn brain)."""
    out = []
    for f in sorted((config.BASE / "private" / "lark-bot-state").glob("dm-session*.txt")):
        try:
            sid = f.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        p = next((Path.home() / ".claude" / "projects").glob(f"*/{sid}.jsonl"), None) if _SID_RE.fullmatch(sid) else None
        if p and p not in out:
            out.append(p)
    return out

_DM_SYS_RE = re.compile(r"^\[Hệ thống: bot đã nâng cấp.*?\]\n\n", re.S)
_DM_GROUP_RE = re.compile(r'^\[Chủ brain @bot trong nhóm "(.*?)"\]\n\n')
_DM_NOTE_RE = re.compile(r"^\(Câu trả lời của bạn được gửi thẳng vào nhóm này.*?\)\n\n", re.S)
_UNTRUSTED_BLOCK_RE = re.compile(r"<untrusted>.*?(?:</untrusted>|$)", re.S)

def dm_owner_text(text):
    """(lời chủ brain, tên nhóm | "") từ một lượt user của phiên DM. Bỏ phần bot chèn (lark_bot.DM_UPGRADED, ghi chú
    nhóm, tin được trả lời/tin gốc của người khác, danh sách ảnh/tệp): những phần đó không phải lời chủ brain."""
    t = _DM_SYS_RE.sub("", text, count=1)
    m = _DM_GROUP_RE.match(t)
    group = m.group(1) if m else ""
    if m:
        t = _DM_NOTE_RE.sub("", t[m.end():], count=1)
    t = re.split(r"\n\n(?:Tin chủ brain đang trả lời|Tin gốc của thread) \(", t)[0]
    t, media, _ = t.partition("\n\nTin có kèm ảnh/tệp")
    t = _UNTRUSTED_BLOCK_RE.sub("", t).strip()
    return (t + (" [kèm ảnh/tệp]" if media else "")).strip(), group

def learn_dm_turns(since, offsets):
    """Lượt mới trong phiên DM từ lần đọc trước: [(epoch, "owner" | "bot", text, nhóm)]. Chỉ đọc phần file sau
    offsets[session_id] (cập nhật tại chỗ, tới dòng hoàn chỉnh cuối), và chỉ lượt sau `since`.
    Bot chỉ đưa vào phiên này tin có sender = OWNER_OPEN_ID (DM.handle), nên lượt user là lời chủ brain."""
    turns = []
    for path in learn_dm_transcripts():
        off = int(offsets.get(path.stem) or 0)
        if off > path.stat().st_size:
            off = 0
        with open(path, "rb") as f:
            f.seek(off)
            data = f.read()
        end = data.rfind(b"\n") + 1
        offsets[path.stem] = off + end
        for raw in data[:end].splitlines():
            try:
                o = json.loads(raw)
            except ValueError:
                continue
            role, origin = o.get("type"), (o.get("origin") or {}).get("kind")
            if (role not in ("user", "assistant") or o.get("isSidechain") or o.get("isMeta")
                    or o.get("isCompactSummary") or (origin and origin != "human")):
                continue
            try:
                ts = datetime.fromisoformat(str(o.get("timestamp")).replace("Z", "+00:00")).timestamp()
            except ValueError:
                continue
            c = (o.get("message") or {}).get("content")
            if ts < since or not c:
                continue
            if isinstance(c, list):
                if any(isinstance(x, dict) and x.get("type") == "tool_result" for x in c):
                    continue
                c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
            if not isinstance(c, str) or not c.strip():
                continue
            if role == "user":
                text, group = dm_owner_text(c)
                if text:
                    turns.append((ts, "owner", text, group))
            else:
                turns.append((ts, "bot", c.strip(), ""))
    return sorted(turns, key=lambda t: t[0])

_OWNER_HEAD_RE = re.compile(r"^(?:USER|LARK-USER)(?=$|[\s(\[])")

def owner_turns(md):
    """[(heading, lời)] của chủ brain trong một file inbox: `### USER` (Claude Code) và `### LARK-USER` (Lark: collect
    gắn theo open_id của lark-cli whoami, bot gắn theo OWNER_OPEN_ID). Lời người khác nằm dưới heading khác
    (LARK-OTHER, CLAUDE, AGENT...) hoặc trong <untrusted> (đã trung hoà `#`, không giả được heading) nên không lọt vào."""
    out = []
    for blk in re.split(r"^### ", md or "", flags=re.M)[1:]:
        head, _, body = blk.partition("\n")
        if _OWNER_HEAD_RE.match(head.strip()):
            body = _UNTRUSTED_BLOCK_RE.sub("", body).strip()
            if body:
                out.append((head.strip(), body))
    return out

def learn_input(since, st=None, path=None):
    """Gom việc mới từ `since` vào logs/learn/input.md cho Claude đọc. Trả dict đếm từng nguồn (rỗng = không có gì
    mới). st: state learn, offset phiên DM được cập nhật tại chỗ. Lời chủ brain gom riêng một mục: chỉ mục đó
    được thành luật/bài học; mọi thứ khác bọc <untrusted>."""
    st = {} if st is None else st
    path = path or (config.LOGS / "learn") / "input.md"
    parts, owner, n = [], [], {}
    turns = learn_dm_turns(since, st.setdefault("dm_offsets", {}))
    for ts, who, text, group in turns:
        if who == "owner":
            where = f"@bot trong nhóm {textsafe.one_line(group, 60)}" if group else "DM bot"
            owner.append((f"LARK-USER ({where}, {datetime.fromtimestamp(ts):%Y-%m-%d %H:%M})", text))
    if turns:
        n["dm"] = len(turns)
        convo = "\n".join(f"[{datetime.fromtimestamp(ts):%m-%d %H:%M}] "
                          + (f"chủ brain: {t[:1500]}" if who == "owner" else f"bot: {t[:600]}")
                          for ts, who, t, _ in turns[-80:])
        parts.append("## Phiên DM chủ brain ↔ bot (ngữ cảnh; lời chủ brain đã chép ở mục trên)\n" + textsafe.untrusted(textsafe.redact(convo)))
    commits = [l for l in util.git("log", f"--since={int(since)}", "--format=%h %s").stdout.splitlines()
               if l.strip() and not l.partition(" ")[2].startswith("learn ")]   # commit của chính learn không phải việc mới
    if commits:
        n["commits"] = len(commits)
        parts.append("## Commit mới\n" + "\n".join(commits))
    files = sorted((p for p in [*config.INBOX.glob("*.md"), *config.INBOX.glob("done/*.md"), *config.LOCAL_INBOX.rglob("*.md")]
                    if p.stat().st_mtime > since), key=lambda p: p.stat().st_mtime)
    for p in files:
        raw, rel = p.read_text(encoding="utf-8", errors="replace"), p.relative_to(config.BASE).as_posix()
        owner += [(f"{head} — {rel}", body) for head, body in owner_turns(raw)]
        parts.append(f"## {rel}\n" + textsafe.untrusted(textsafe.redact(raw[-6000:])))
    if files:
        n["files"] = len(files)
    bot = _bot_log(since)
    if bot:
        n["bot_log"] = len(bot)
        parts.append("## Log bot Lark (lỗi, im, chỉ tag)\n" + textsafe.redact("\n".join(bot)))
    runs = [l for l in (config.LOGS / "run.log").read_text(encoding="utf-8", errors="replace").splitlines()[-300:]
            if "ok=False" in l and l[:19] >= datetime.fromtimestamp(since).strftime("%Y-%m-%dT%H:%M:%S")] \
        if (config.LOGS / "run.log").exists() else []
    if runs:
        n["job_errors"] = len(runs)
        parts.append("## Job lỗi\n" + textsafe.redact("\n".join(runs)))
    if owner:
        n["owner"] = len(owner)
    log_lines = [l for l in (config.BASE / "LOG.md").read_text(encoding="utf-8", errors="replace").splitlines()
                 if l.startswith("- ") and l[2:12] >= datetime.fromtimestamp(since).strftime("%Y-%m-%d")]
    said = "".join(f"### {h}\n" + re.sub(r"(?m)^(\s*)[#＃]", r"\1\\#", textsafe.redact(b[:2000])) + "\n\n" for h, b in owner[-40:])
    head = (f"# Đầu vào learn từ {datetime.fromtimestamp(since):%Y-%m-%d %H:%M}\n\n"
            "## Dòng LOG.md gần đây (để không học trùng)\n" + "\n".join(log_lines[-40:]) + "\n\n"
            "## Lời chủ brain (USER/LARK-USER, đúng open_id): CHỈ mục này được thành luật/bài học\n"
            + (said or "Không có lời mới của chủ brain.\n\n"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(head + "\n\n".join(parts)[-LEARN_MAX:], encoding="utf-8")
    return n


def learn_lark_collect(st, dm, dry=False):
    """Kéo tin Lark mới (allowlist) trước mỗi lượt learn. lark-cli lỗi xác thực: DM chủ brain đúng 1 lần, các lượt sau
    vẫn thử (một lệnh whoami, rẻ) nhưng im, kéo được lại thì xoá cờ. Trả mô tả ngắn cho log / --dry."""
    if not larkcli._read_lark_allow():
        return "bỏ qua (allowlist trống)"
    try:
        rc = larkcollect.cmd_lark_collect(dry=dry)
        err = {0: "", 2: "thiếu scope", 3: larkcli.LARK_AUTH_HINT}.get(rc, f"rc={rc}")
    except Exception as e:   # lỗi Lark không được làm hỏng lượt learn
        rc, err = 1, str(e)
    if rc == 0:
        if st.pop("lark_auth_alerted", None):
            util.log("learn: lark-cli hết lỗi xác thực, kéo tin Lark lại bình thường")
        return "ok" + (" (dry-run)" if dry else "")
    if rc in (2, 3) or larkcli.lark_auth_error(err):
        if not st.get("lark_auth_alerted"):
            dm(f"⚠️ Job learn: cần đăng nhập lại lark-cli trên máy {config.HOST} ({textsafe.one_line(textsafe.redact(err), 160)}). "
               "E bỏ qua bước kéo tin Lark tới khi hết lỗi, không báo lại.")
            st["lark_auth_alerted"] = time.time()
        return "lỗi xác thực lark-cli, bỏ qua"
    util.log(f"learn: lark collect lỗi: {textsafe.one_line(textsafe.redact(err), 200)}")
    return f"lỗi ({textsafe.one_line(err, 80)}), bỏ qua"
