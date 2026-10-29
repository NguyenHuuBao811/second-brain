"""argparse + main của scripts/brain.py."""
import argparse
import json
import sys
from pathlib import Path
import brain_kb
from hibrain import SCRIPTS_DIR
from . import agentapi, chatlogs, claudecli, config, dispatching, factcheck, larkcli, larkcollect, larkdraft, larkjudge, learnrun, migrate, persona, runjobs, setup, upgrade, util

def main():
    ap = argparse.ArgumentParser(description="Second brain CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("job", choices=["ingest", "reflect", "lint", "eval", "prune", "learn"])
    r.add_argument("--model", default="sonnet")
    r.add_argument("--no-sync", action="store_true")
    r.add_argument("--force", action="store_true", help="chạy kể cả khi máy khác đã chạy kỳ này")
    r.add_argument("--batch", type=int, help="ingest: số file một lượt (mặc định 5; trần lượt/USD tăng theo)")
    r.add_argument("--dry", action="store_true", help="learn: in ra điều sẽ ghi và sẽ DM, không ghi, không gửi")
    sub.add_parser("sync")
    ld = sub.add_parser("learn-day", help="DM chủ brain tổng hợp cả ngày job learn đã học + danh sách chờ duyệt (lịch 17:45)")
    ld.add_argument("--model", default="sonnet")
    ld.add_argument("--dry", action="store_true", help="in tin sẽ DM, không gửi")
    co = sub.add_parser("collect", help="gom chat Claude và git mới vào 00-inbox")
    co.add_argument("--days", type=int, default=2)
    co.add_argument("--max-files", type=int, default=30)
    co.add_argument("--min-user", type=int, default=3, help="bỏ phiên có ít hơn N lời người dùng")
    co.add_argument("--settle", type=int, default=60, help="bỏ phiên vừa ghi trong N phút gần đây")
    co.add_argument("--dry-run", action="store_true")
    co.add_argument("--allow", metavar="DIR", help="cho phép gom chat của dự án này")
    co.add_argument("--disallow", metavar="DIR", help="ngừng gom dự án này")
    co.add_argument("--list", action="store_true", help="xem danh sách dự án được gom")
    c = sub.add_parser("chats")
    c.add_argument("--days", type=int, default=30)
    g = sub.add_parser("git")
    g.add_argument("repo")
    g.add_argument("--since", default="6 months ago")
    s = sub.add_parser("schedule")
    s.add_argument("action", choices=["install", "uninstall", "status"])
    s.add_argument("--jobs", default="collect,ingest,reflect,lint,sync,prune,verify")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--os", choices=["Darwin", "Linux", "Windows"], help="chỉ dùng với --dry-run")
    lk = sub.add_parser("lark", help="kéo chat Lark (allowlist) vào 00-inbox/local/lark; send: bot gửi thông báo; "
                        "draft/feedback: cho bot soạn nháp nhóm (JSON qua stdin)")
    lk.add_argument("action", choices=["chats", "collect", "send", "draft", "feedback", "shadow-report", "voice", "members"])
    lk.add_argument("target", nargs="?", help="members: chat_id hoặc tên nhóm trong allowlist")
    lk.add_argument("--json", action="store_true", help="members: in JSON")
    lk.add_argument("--model", default=None, help="draft: model soạn nháp (sonnet); voice: model chưng cất (opus)")
    lk.add_argument("--chat", help="send: tên nhóm hoặc chat_id mà bot đang ở")
    lk.add_argument("--text", help="send: nội dung tin")
    lk.add_argument("--text-file", help="send: đọc nội dung tin từ file")
    lk.add_argument("--file", help="send: đính kèm 1 file")
    lk.add_argument("--send", action="store_true", help="send: gửi thật (mặc định chỉ dry-run)")
    lk.add_argument("--allow", metavar="CHAT_ID")
    lk.add_argument("--remove", metavar="CHAT_ID")
    lk.add_argument("--days", type=int, default=30, help="lần đầu kéo N ngày gần nhất")
    lk.add_argument("--min-user", type=int, default=2, help="bỏ chat có ít hơn N tin của chủ brain")
    lk.add_argument("--dry-run", action="store_true")
    sub.add_parser("doctor")
    cm = sub.add_parser("commit", help="commit file nội dung vault (dùng cho bot Lark): commit -m MSG FILE...")
    cm.add_argument("-m", "--message", required=True)
    cm.add_argument("files", nargs="*")
    sub.add_parser("status", help="file đã đổi chưa lưu (git status + diff --stat; không git: so với bản chụp cuối)")
    rg = sub.add_parser("register", help="ghi máy này vào machines.md, mọi máy đều ghi được")
    rg.add_argument("role", nargs="?", help=argparse.SUPPRESS)  # primary/secondary cũ, bỏ qua
    rg.add_argument("--force", action="store_true", help=argparse.SUPPRESS)
    sub.add_parser("context", help="in phần agent nên đọc đầu session")
    se = sub.add_parser("search", help="tìm trong brain theo từ khoá")
    se.add_argument("query", nargs="+")
    se.add_argument("--limit", type=int, default=20)
    rd = sub.add_parser("read", help="in một file trong brain")
    rd.add_argument("path")
    cp = sub.add_parser("capture", help="agent gửi ghi chú vào 00-inbox (đọc nội dung từ stdin)")
    cp.add_argument("--title", required=True)
    cp.add_argument("--agent", default="agent")
    sub.add_parser("mcp-config", help="in cấu hình MCP cho Claude Code, Codex, Gemini CLI, Cursor")
    ck = sub.add_parser("check", help="kiểm tất định (không LLM): mồ côi, link chết, frontmatter, stale, INDEX lệch")
    ck.add_argument("--backfill", action="store_true", help="thêm last_verified = updated cho file cũ chưa có")
    ck.add_argument("--json", action="store_true")
    gp = sub.add_parser("gaps", help="câu hỏi brain không trả lời được + dự án có mục trống")
    gp.add_argument("--days", type=int, default=7)
    gp.add_argument("--write", action="store_true", help="ghi 00-inbox/gaps-YYYY-Www.md (mỗi tuần một file)")
    ix = sub.add_parser("index", help="index <mảng>: in chỉ mục con; index --build: tách INDEX lõi + indexes/")
    ix.add_argument("area", nargs="?")
    ix.add_argument("--build", action="store_true")
    ix.add_argument("--dry", action="store_true", help="--build: chỉ in kích thước, không ghi")
    vs = sub.add_parser("verify-sample", help="agent khác đối chiếu N fact ngẫu nhiên với bản gốc (trần 1 USD)")
    vs.add_argument("--n", type=int, default=10)
    vs.add_argument("--dry", action="store_true")
    vs.add_argument("--model", help="mặc định BRAIN_VERIFY_MODEL hoặc opus")
    vs.add_argument("--budget", type=float, default=factcheck.VERIFY_BUDGET)
    vs.add_argument("--seed", type=int)
    vs.add_argument("--sync", action="store_true", help="pull trước, push sau (job tuần)")
    cf = sub.add_parser("conflicts", help="fact cùng đối tượng + thuộc tính mà giá trị khác nhau")
    cf.add_argument("--apply", action="store_true", help="ghi vào eval/review-queue.md (mục Mâu thuẫn)")
    ri = sub.add_parser("reingest", help="chạy lại ingest từ kho raw (mặc định dry-run)")
    ri.add_argument("raw_id", nargs="?")
    ri.add_argument("--since", help="YYYY-MM-DD")
    ri.add_argument("--apply", action="store_true")
    ev = sub.add_parser("eval", help="chạy câu hỏi vàng: độ chính xác, thời gian, token mỗi câu (trần --budget USD)")
    ev.add_argument("--n", type=int)
    ev.add_argument("--model", default="sonnet")
    ev.add_argument("--budget", type=float, default=2.0)
    ev.add_argument("--dry", action="store_true")
    ev.add_argument("--set", choices=["golden", "golden-lark", "all"], default="all")
    qa = sub.add_parser("qa", help="qa find <câu hỏi>: bản trả lời đã lưu; qa prune [--apply]: dọn bản quá hạn")
    qa.add_argument("action", choices=["find", "prune"])
    qa.add_argument("question", nargs="*")
    qa.add_argument("--apply", action="store_true")
    hb = sub.add_parser("hub", help="hub new <person|project|system> <tên> | hub sync (backlinks trong Xem thêm)")
    hb.add_argument("action", choices=["new", "sync"])
    hb.add_argument("kind", nargs="?")
    hb.add_argument("name", nargs="*")
    hb.add_argument("--dry", action="store_true", help="sync: chỉ liệt kê hub sẽ đổi")
    rp = sub.add_parser("raw-prune", help="bản gốc quá hạn giữ (BRAIN_RAW_KEEP_DAYS, mặc định 180)")
    rp.add_argument("--days", type=int)
    rp.add_argument("--apply", action="store_true", help="xoá thật (cần chủ brain xác nhận)")
    sub.add_parser("set-token")
    it = sub.add_parser("init", help="tạo brain mới từ khung")
    it.add_argument("target")
    it.add_argument("--template", default=str(SCRIPTS_DIR.parent))
    it.add_argument("--name")
    it.add_argument("--owner")
    it.add_argument("--role")
    it.add_argument("--priorities")
    it.add_argument("--no-git", action="store_true", help="không dùng git: lưu bằng bản chụp logs/snapshots/")
    hi = sub.add_parser("history", help="các lần lưu (git log, hoặc bản chụp khi không có git)")
    hi.add_argument("--limit", type=int, default=20)
    rs = sub.add_parser("restore", help="khôi phục dữ liệu về bản chụp <số> (brain không có git)")
    rs.add_argument("number", type=int)
    sub.add_parser("locate", help="liệt kê brain đã có trên máy này")
    up = sub.add_parser("upgrade", help="so một brain có sẵn với khung, bổ sung phần còn thiếu")
    up.add_argument("target", help="thư mục brain cần nâng cấp")
    up.add_argument("--template", required=True, help="thư mục khung (assets/template của skill)")
    up.add_argument("--apply", action="store_true", help="ghi thay đổi ADD/UPDATE (mặc định chỉ báo cáo)")
    up.add_argument("--skip-update", action="store_true", help="chỉ thêm phần thiếu, giữ nguyên file điều khiển đã sửa riêng")
    mg = sub.add_parser("migrate", help="chuyển dữ liệu từ brain cấu trúc khác (second-brain-lite, thư mục .md) sang brain này")
    mg.add_argument("source", help="thư mục brain nguồn (chỉ đọc)")
    mg.add_argument("--into", default=str(config.BASE), help="brain đích (mặc định brain chứa script này)")
    mg.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ báo cáo)")
    dp = sub.add_parser("dispatch", help="giao việc cho agent chạy trong repo của một dự án")
    dp.add_argument("project", help="tên dashboard trong 20-projects/, không có .md")
    dp.add_argument("task", help="mô tả việc")
    dp.add_argument("--edit", action="store_true", help="cho sửa file + commit trên branch mới (mặc định chỉ lập kế hoạch)")
    dp.add_argument("--allow", action="append", default=[], help='thêm tool, vd "Bash(npm test:*)"; lặp lại được')
    dp.add_argument("--model")
    dp.add_argument("--budget", type=float, default=5.0, help="trần USD mỗi lần")
    dp.add_argument("--dry-run", action="store_true", help="in lệnh và prompt, không chạy")
    pe = sub.add_parser("persona-eval", help="đo brain mô phỏng chủ nhân giống tới đâu")
    pe.add_argument("--n", type=int, default=10, help="số câu thật để thử")
    pe.add_argument("--model", default="sonnet", help="model mô phỏng")
    pe.add_argument("--judge-model", default="opus", help="model giám khảo, nên khác hoặc mạnh hơn")
    pe.add_argument("--min-chars", type=int, default=25, help="bỏ câu quá ngắn như 'ok', 'tiếp đi'")
    pe.add_argument("--seed", type=int, default=7)
    pe.add_argument("--no-baseline", action="store_true", help="bỏ agent không có brain")
    pe.add_argument("--chats", default="*.md", help="glob trong raw/chats, ví dụ '*catalog*'")
    pe.add_argument("--source", choices=["claude", "lark"], default="claude",
                    help="lark: đoán tin chủ brain gửi team sau mốc T (eval/lark-holdout.txt)")
    a = ap.parse_args()

    if a.cmd == "locate":
        brains = upgrade.locate_brains()
        for d, jobs in brains.items():
            print(f"{d}    jobs: {', '.join(jobs) or '(chưa cài lịch)'}")
        lite = upgrade.locate_lite_brains()
        for d in lite:
            print(f"{d}    second-brain-lite (cấu trúc khác: chuyển sang bằng `migrate {d}`)")
        if not brains and not lite:
            print("(không có brain nào trên máy này)")
        return 0
    if a.cmd == "upgrade":
        return upgrade.cmd_upgrade(a.target, a.template, a.apply, a.skip_update)
    if a.cmd == "migrate":
        return migrate.cmd_migrate(a.source, a.into, a.apply)
    if a.cmd == "dispatch":
        return dispatching.cmd_dispatch(a.project, a.task, "edit" if a.edit else "plan", a.allow, a.model, a.budget,
                            dry=a.dry_run)
    if a.cmd == "persona-eval":
        return persona.cmd_persona_eval(a.n, a.model, a.judge_model, None, a.min_chars, a.seed,
                                not a.no_baseline, a.chats, a.source)
    if a.cmd == "init":
        return setup.cmd_init(a.target, a.template, a.name, a.owner, a.role, a.priorities, not a.no_git)
    if a.cmd == "history":
        return util.cmd_history(a.limit)
    if a.cmd == "restore":
        return util.cmd_restore(a.number)
    if a.cmd == "register":
        return setup.cmd_register()
    if a.cmd == "context":
        print(agentapi.brain_context())
        return 0
    if a.cmd == "search":
        for h in agentapi.brain_search(" ".join(a.query), a.limit):
            print(f"{h['path']}:{h['line']}: {h['text']}")
        return 0
    if a.cmd == "read":
        try:
            print(agentapi.brain_read(a.path))
        except ValueError as e:
            sys.exit(f"!! {e}")
        return 0
    if a.cmd == "capture":
        body = sys.stdin.read().strip()
        if not body:
            sys.exit("!! nội dung rỗng (đọc từ stdin)")
        print(agentapi.brain_capture(a.title, body, a.agent))
        return 0
    if a.cmd == "mcp-config":
        print(agentapi.mcp_config())
        return 0
    if a.cmd == "check":
        return agentapi.cmd_check(a.backfill, a.json)
    if a.cmd == "index":
        return factcheck.cmd_index(a.area, a.build, a.dry)
    if a.cmd == "verify-sample":
        return factcheck.cmd_verify_sample(a.n, a.dry, a.model, a.budget, a.seed, a.sync)
    if a.cmd == "conflicts":
        return factcheck.cmd_conflicts(a.apply)
    if a.cmd == "reingest":
        if not a.raw_id and not a.since:
            sys.exit("!! cần <raw_id> hoặc --since YYYY-MM-DD")
        return factcheck.cmd_reingest(a.raw_id, a.since, a.apply)
    if a.cmd == "raw-prune":
        return factcheck.cmd_raw_prune(a.days, a.apply)
    if a.cmd == "eval":
        return claudecli.cmd_eval(a.n, a.model, a.budget, a.dry, ("golden", "golden-lark") if a.set == "all" else (a.set,))
    if a.cmd == "qa":
        return factcheck.cmd_qa(a.action, " ".join(a.question), a.apply)
    if a.cmd == "hub":
        return factcheck.cmd_hub(a.action, a.kind, " ".join(a.name), apply=not a.dry)
    if a.cmd == "gaps":
        if a.write:
            p = brain_kb.write_weekly_gaps(config.BASE, config.LOGS, config.BASE / "00-inbox", verify=runjobs.latest_verify())
            print(p.relative_to(config.BASE).as_posix() if p else "tuần này đã có báo cáo gaps")
            return 0
        print(brain_kb.gaps_report(config.BASE, config.LOGS, a.days, runjobs.latest_verify()))
        return 0
    if a.cmd == "set-token":
        return setup.cmd_set_token()
    if a.cmd == "commit":
        return setup.cmd_commit(a.message, a.files)
    if a.cmd == "status":
        return setup.cmd_status()

    if a.cmd == "run":
        return runjobs.cmd_run(a.job, a.model, not a.no_sync, a.force, a.batch, a.dry)
    if a.cmd == "sync":
        return util.cmd_sync()
    if a.cmd == "learn-day":
        return learnrun.cmd_learn_day(a.model, dry=a.dry)
    if a.cmd == "collect":
        if a.allow or a.disallow or a.list:
            return chatlogs.cmd_collect_allow(a.allow, a.disallow)
        return chatlogs.cmd_collect(a.days, a.max_files, a.min_user, a.settle, a.dry_run)
    if a.cmd == "chats":
        return chatlogs.cmd_chats(a.days)
    if a.cmd == "lark":
        if a.action == "chats":
            return larkcli.cmd_lark_chats(a.allow, a.remove)
        if a.action == "send":
            if not a.chat:
                sys.exit("!! cần --chat")
            text = Path(a.text_file).expanduser().read_text(encoding="utf-8").strip() if a.text_file else a.text
            return agentapi.cmd_lark_send(a.chat, text, a.file, a.send)
        if a.action == "draft":
            print(json.dumps(larkdraft.lark_draft(json.load(sys.stdin), a.model or "sonnet"), ensure_ascii=False))
            return 0
        if a.action == "shadow-report":
            return larkjudge.cmd_lark_shadow_report()
        if a.action == "members":
            if not a.target:
                sys.exit("!! cần chat_id hoặc tên nhóm: brain.py lark members <chat_id|tên nhóm>")
            return larkcollect.cmd_lark_members(a.target, a.json)
        if a.action == "voice":
            return larkjudge.cmd_lark_voice(a.model or "opus")
        if a.action == "feedback":
            print(json.dumps({"path": str(larkdraft.lark_feedback_write(json.load(sys.stdin)))}, ensure_ascii=False))
            return 0
        return larkcollect.cmd_lark_collect(a.days, a.min_user, a.dry_run)
    if a.cmd == "git":
        return setup.cmd_git(a.repo, a.since)
    if a.cmd == "schedule":
        jobs = [j.strip() for j in a.jobs.split(",") if j.strip()]
        bad = [j for j in jobs if j not in config.JOBS]
        if bad:
            sys.exit(f"unknown jobs: {bad}")
        return setup.cmd_schedule(a.action, jobs, a.dry_run, a.os if a.dry_run else None)
    if a.cmd == "doctor":
        return setup.cmd_doctor()
