"""Lark: thành viên, collect, fetch tin/thread, tên, open_id."""
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from . import chatlogs, larkcli, textsafe, util

def cmd_lark_members(target, as_json=False, get=None):
    """Thành viên là người của một nhóm trong allowlist: tên | email | open_id. Chỉ đọc, không ghi file."""
    get = get or larkcli._lark_get_any
    rows = larkcli._lark_allow_rows()
    norm = lambda t: " ".join(str(t).lower().split()).replace(" ", "")
    hit = [r for r in rows if r[0] == target] or [r for r in rows if norm(r[2]) == norm(target)]
    if len(hit) != 1:
        print(f"!! '{target}' không có trong allowlist (private/lark-chats.txt) hoặc trùng tên. "
              "Xem: `brain.py lark chats`, thêm: `brain.py lark chats --allow <chat_id>`.", file=sys.stderr)
        return 2
    cid = hit[0][0]
    members, token = [], ""
    try:
        while True:
            params = {"member_id_type": "open_id", "page_size": 100, **({"page_token": token} if token else {})}
            d = get(f"/open-apis/im/v1/chats/{cid}/members", params).get("data") or {}
            members += [(m["member_id"], m.get("name") or "") for m in d.get("items") or []
                        if m.get("member_id_type", "open_id") == "open_id" and str(m.get("member_id", "")).startswith("ou_")
                        and m.get("member_type", "user") == "user"]
            token = d.get("page_token") or ""
            if not d.get("has_more") or not token:
                break
    except larkcli.LarkScopeError as e:
        print(f"!! thiếu quyền đọc thành viên nhóm. Cần scope: {e}", file=sys.stderr)
        return 2
    out, missing = [], set()
    for oid, name in members:
        email = ""
        try:
            u = (get(f"/open-apis/contact/v3/users/{oid}", {"user_id_type": "open_id"}).get("data") or {}).get("user") or {}
            name = u.get("name") or name
            email = u.get("enterprise_email") or u.get("email") or ""
            if not email:
                missing.add("contact:user.email:readonly (API không trả email: thiếu scope hoặc người này không có email)")
        except larkcli.LarkScopeError as e:
            missing.add(f"{e}; email cần thêm contact:user.email:readonly")
        out.append({"name": name, "email": email, "open_id": oid})
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("tên | email | open_id")
        for r in out:
            print(f"{r['name']} | {r['email']} | {r['open_id']}")
    for m in sorted(missing):
        print(f"!! không lấy được email, cần xin: {m}. Email để trống, không đoán.", file=sys.stderr)
    return 0

def cmd_lark_collect(days=30, min_user=2, dry=False):
    """Kéo tin mới của các chat trong allowlist về 00-inbox/local/lark/ (gitignore).

    - Incremental: nhớ thời điểm tin cuối mỗi chat trong private/lark-state.json.
    - Dừng ở mốc T (eval/lark-holdout.txt): tin sau T dành cho đo.
    - Bỏ chat có ít hơn min_user tin của chủ brain trong lần kéo.
    - Xoá raw Lark quá 30 ngày.
    """
    allow = larkcli._read_lark_allow()
    if not allow:
        util.log("lark: allowlist trống. Xem chat: `brain.py lark chats`, thêm: `--allow <chat_id>`.")
        return 0
    try:
        my_id = _lark_my_id()
    except RuntimeError as e:
        if larkcli.lark_auth_error(e):
            util.log(f"lark: {larkcli.LARK_AUTH_HINT} ({textsafe.redact(str(e))[:200]})")
            return 3
        raise
    names = _lark_names()
    try:
        state = json.loads(larkcli.LARK_STATE.read_text(encoding="utf-8"))
    except Exception:
        state = {}
    end = larkcli._lark_holdout_cutoff()
    # Lần đầu: lấy `days` ngày ngay trước mốc T (hoặc trước hôm nay nếu chưa có T).
    base_ts = datetime.strptime(end, "%Y-%m-%d").timestamp() if end else time.time()
    default_start = datetime.fromtimestamp(base_ts - days * 86400).strftime("%Y-%m-%d")
    written, auth_lost = [], False
    for cid, name in allow.items():
        start = state.get(cid) or default_start
        if end and start >= end:
            continue
        try:
            msgs = _lark_fetch(cid, start, end)
        except larkcli.LarkScopeError as e:
            util.log(f"lark: thiếu quyền {e}. Chạy: lark-cli auth login --scope \"{e}\"")
            return 2
        except RuntimeError as e:
            if not larkcli.lark_auth_error(e):
                raise
            util.log(f"lark: {larkcli.LARK_AUTH_HINT} ({textsafe.redact(str(e))[:200]}); mốc kéo tin giữ nguyên")
            auth_lost = True
            break
        if state.get(cid):  # --start lấy cả tin cuối lần trước: bỏ đi
            msgs = [m for m in msgs if _lark_ts(m) > state[cid]]
        if not msgs:
            continue
        md, n_user = larkcli.lark_messages_to_md(name or cid, msgs, my_id, names)
        newest = max(_lark_ts(m) for m in msgs)
        if md and n_user >= min_user:
            slug = re.sub(r"[^a-z0-9]+", "-", (name or cid).lower()).strip("-")[:40] or cid[-8:]
            stem = f"lark-{slug}-{datetime.now():%Y%m%d-%H%M}"
            parts = chatlogs.split_chat(md)
            for i, part in enumerate(parts, 1):
                fn = f"{stem}.md" if len(parts) == 1 else f"{stem}-p{i}of{len(parts)}.md"
                written.append(fn)
                if not dry:
                    larkcli.LARK_INBOX.mkdir(parents=True, exist_ok=True)
                    (larkcli.LARK_INBOX / fn).write_text(part, encoding="utf-8")
        if not dry:
            state[cid] = newest
    pruned = 0 if dry else larkcli._lark_prune_raw()
    if not dry:
        larkcli.LARK_STATE.parent.mkdir(exist_ok=True)
        larkcli.LARK_STATE.write_text(json.dumps(state, indent=1), encoding="utf-8")
    util.log(f"lark: {len(written)} files -> 00-inbox/local/lark (không vào git)"
        + (f", mốc holdout T={end}" if end else "") + (f", xoá {pruned} raw cũ" if pruned else "")
        + (" (dry-run)" if dry else ""))
    for n in written if dry else []:
        print("  ", n)
    return 3 if auth_lost else 0

def _lark_fetch(cid, start, end=None, max_pages=40, sort="ByCreateTimeAsc"):
    """Tin của một chat qua API thô (lệnh +chat-messages-list đòi thêm scope reaction).
    start/end: 'YYYY-MM-DD' hoặc 'YYYY-MM-DDTHH:MM:SS' giờ máy. Không gồm tin trả lời trong thread: xem _lark_fetch_thread."""
    def secs(t):
        return str(int(datetime.fromisoformat(t).timestamp()))
    params = {"container_id_type": "chat", "container_id": cid, "page_size": 50,
              "sort_type": sort, "start_time": secs(start)}
    if end:
        params["end_time"] = secs(end)
    out = []
    for _ in range(max_pages):
        d = larkcli._lark("api", "GET", "/open-apis/im/v1/messages", "--params", json.dumps(params)).get("data", {})
        out += d.get("items") or []
        if not d.get("has_more") or not d.get("page_token"):
            break
        params["page_token"] = d["page_token"]
    return out

def _lark_fetch_thread(tid, after_ms, max_pages=5):
    """Tin trong một thread (omt_...) mới hơn after_ms, cũ → mới. Thread không lọc được theo giờ nên đọc từ mới
    nhất về và dừng khi gặp tin cũ."""
    params = {"container_id_type": "thread", "container_id": tid, "page_size": 50, "sort_type": "ByCreateTimeDesc"}
    out = []
    for _ in range(max_pages):
        d = larkcli._lark("api", "GET", "/open-apis/im/v1/messages", "--params", json.dumps(params)).get("data", {})
        items = d.get("items") or []
        out += [m for m in items if int(m.get("create_time") or 0) > after_ms]
        if not d.get("has_more") or not d.get("page_token") or any(int(m.get("create_time") or 0) <= after_ms for m in items):
            break
        params["page_token"] = d["page_token"]
    return out[::-1]

def _lark_resource(mid, key, kind, out):
    """Tải ảnh/tệp của một tin về file `out` (API thô: lệnh tắt +messages-resources-download đòi thêm scope)."""
    larkcli._lark("api", "GET", f"/open-apis/im/v1/messages/{mid}/resources/{key}", "--params", json.dumps({"type": kind}),
          "--output", str(out))
    return Path(out)

def _lark_names():
    """open_id -> tên, lấy từ chat 1-1 (không cần scope contact). Người lạ thì hiện mã rút gọn."""
    try:
        chats = larkcli._lark("im", "+chat-list", "--types=p2p", "--page-all").get("data", {}).get("chats", [])
    except Exception:
        return {}
    return {c["p2p_target_id"]: c.get("name", "") for c in chats if c.get("p2p_target_id")}

def _lark_ts(m):
    """create_time của tin dạng 'YYYY-MM-DDTHH:MM:SS' để so sánh chuỗi; nhận cả epoch ms."""
    t = str(m.get("create_time", ""))
    if t.isdigit():
        return datetime.fromtimestamp(int(t) / 1000).strftime("%Y-%m-%dT%H:%M:%S")
    return t[:19].replace(" ", "T")

def _lark_my_id():
    exe = larkcli.find_lark_cli()
    if not exe:
        raise RuntimeError("không thấy lark-cli")
    r = subprocess.run([exe, "whoami"], capture_output=True, text=True, encoding="utf-8", timeout=60, env=larkcli.lark_cli_env(exe))
    try:
        return json.loads(r.stdout)["onBehalfOf"]["openId"]
    except Exception:
        raise RuntimeError("không lấy được open_id: chạy `lark-cli auth status`")
