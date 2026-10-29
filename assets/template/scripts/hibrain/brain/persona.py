"""persona eval: chọn case, prompt mô phỏng, chấm."""
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from . import claudecli, config, larkcli, larkcollect, util

# ---------------------------------------------------------------- persona eval
# Đo brain hiểu chủ nhân tới đâu: lấy câu thật chủ brain đã nói trong chat, cho một agent
# chỉ dùng brain đoán câu đó, rồi một agent thứ ba chấm mù hai câu.

PERSONA_DIR = "persona"  # eval/persona/<ngày>/


def _turns(md):
    """Tách file chat (định dạng của session_to_md) thành list (speaker, text)."""
    out = []
    for blk in re.split(r"^### ", md, flags=re.M)[1:]:
        head, _, body = blk.partition("\n")
        out.append((head.split(" (")[0].strip(), body.strip()))
    return out


def _pick_cases(chat_files, n, min_chars, seed):
    """Chọn n lượt USER làm câu hỏi. Ưu tiên câu có thông tin: đủ dài, đứng sau một lượt CLAUDE."""
    import random
    cands = []
    for f in chat_files:
        turns = _turns(Path(f).read_text(encoding="utf-8"))
        for i, (who, text) in enumerate(turns):
            if who != "USER" or len(text) < min_chars or i == 0:
                continue
            prev = [t for t in turns[max(0, i - 6):i] if t[0] in ("USER", "CLAUDE")]
            if not prev or prev[-1][0] != "CLAUDE":
                continue
            # Giữ trọn lượt CLAUDE cuối (người dùng phản hồi chính nó), cắt đầu các lượt cũ hơn.
            # Nếu cắt đuôi lượt cuối, agent mô phỏng sẽ viết tiếp câu của Claude thay vì trả lời.
            def clip(t, n):
                return t if len(t) <= n else "…" + t[-n:]
            ctx = "\n\n".join(f"[{w}]\n{clip(t, 3000 if j == len(prev[-4:]) - 1 else 800)}"
                              for j, (w, t) in enumerate(prev[-4:]))
            cands.append({"source": Path(f).name, "context": ctx, "actual": text[:2000]})
    random.Random(seed).shuffle(cands)
    return cands[:n]


def _pick_lark_cases(chats, n, min_chars, seed):
    """Chọn n tin LARK-USER trả lời ngay sau tin của người khác. chats: list (tên chat, markdown)."""
    import random
    cands = []
    for name, md in chats:
        turns = [(w, re.sub(r"</?untrusted>", "", t).strip()) for w, t in _turns(md)]
        turns = [(re.sub(r"\s*\[om_[^\]]*\]$", "", w), t) for w, t in turns]
        for i, (who, text) in enumerate(turns):
            if who != "LARK-USER" or len(text) < min_chars or i == 0:
                continue
            prev = turns[max(0, i - 6):i]
            if not prev[-1][0].startswith("LARK-OTHER"):
                continue
            def label(w):
                return "CHỦ NHÂN" if w == "LARK-USER" else w.removeprefix("LARK-OTHER:")
            ctx = "\n\n".join(f"[{label(w)}]\n{t[-800:]}" for w, t in prev)
            cands.append({"source": name, "context": ctx, "actual": text[:2000]})
    random.Random(seed).shuffle(cands)
    return cands[:n]


def _lark_holdout_chats():
    """Tin từ mốc T tới nay của các chat trong allowlist. Không ghi ra đĩa, không đi qua ingest."""
    end = larkcli._lark_holdout_cutoff()
    if not end:
        sys.exit("!! chưa có mốc T trong eval/lark-holdout.txt")
    my_id, names, out = larkcollect._lark_my_id(), larkcollect._lark_names(), []
    for cid, name in larkcli._read_lark_allow().items():
        msgs = larkcollect._lark_fetch(cid, end)
        md, n_user = larkcli.lark_messages_to_md(name or cid, msgs, my_id, names)
        if md and n_user:
            out.append((name or cid, md))
    return out


SIM_PROMPT = """Bạn đóng vai chủ nhân của second brain trong thư mục hiện tại.
Đọc AGENTS.md, CRITICAL.md, 50-knowledge/working-preferences.md (nếu có), INDEX.md, rồi chỉ mở file liên quan.
Không đọc raw/, 00-inbox/, eval/, archive/, logs/.

Dưới đây là đoạn hội thoại giữa chủ nhân [USER] và trợ lý AI [CLAUDE]. Lượt cuối là của CLAUDE và đã kết thúc.
Viết tin nhắn tiếp theo mà CHÍNH CHỦ NHÂN sẽ gõ để trả lời lượt cuối đó.

Cách làm:
1. Dùng brain để hiểu chủ nhân: họ làm việc thế nào, hay đồng ý, hỏi lại, nghi ngờ hay giao việc; viết dài hay ngắn.
2. Dùng brain để hiểu bối cảnh, nhưng đừng nhồi fact từ brain vào câu. Người thật chỉ nhắc chi tiết khi cần.
3. Nếu working-preferences.md có mô tả cách viết (ngôn ngữ, độ dài, viết tắt, lỗi gõ), bắt chước đúng như vậy.
4. Bạn là người dùng, không phải trợ lý. Đừng viết tiếp câu của CLAUDE, đừng giải thích, đừng viết như AI.

=== HỘI THOẠI ===
{context}
=== HẾT ===

Chỉ in ra tin nhắn của chủ nhân, không tiền tố, không dấu ngoặc:"""

BASE_PROMPT = """Dưới đây là đoạn hội thoại giữa người dùng [USER] và trợ lý AI [CLAUDE]. Lượt cuối là của CLAUDE và đã kết thúc.
Bạn không biết gì về người dùng này ngoài đoạn hội thoại.
Viết tin nhắn tiếp theo mà người dùng có khả năng nhất sẽ gõ. Bạn là người dùng, không phải trợ lý.

=== HỘI THOẠI ===
{context}
=== HẾT ===

Chỉ in ra tin nhắn của người dùng, không tiền tố, không dấu ngoặc:"""

SIM_LARK_PROMPT = """Bạn đóng vai chủ nhân của second brain trong thư mục hiện tại.
Đọc AGENTS.md, CRITICAL.md, 50-knowledge/owner-model.md (giọng với team), INDEX.md, rồi chỉ mở file liên quan.
Không đọc raw/, 00-inbox/, eval/, archive/, logs/.

Dưới đây là đoạn chat công việc trên Lark giữa chủ nhân [CHỦ NHÂN] và đồng nghiệp (tên trong ngoặc vuông).
Viết tin nhắn tiếp theo mà CHÍNH CHỦ NHÂN sẽ gõ vào nhóm chat này.

Cách làm:
1. Dùng brain để hiểu dự án, ai làm gì, và chủ nhân nói chuyện với team thế nào.
2. Đừng nhồi fact từ brain vào câu. Người thật chỉ nhắc chi tiết khi cần.
3. Bắt chước đúng giọng với team trong owner-model.md: độ dài, viết tắt, có dấu hay không, icon.
4. Bạn là chủ nhân, không phải trợ lý. Đừng giải thích, đừng viết như AI.
5. Dòng đầu tiên bạn in ra đã là tin nhắn gửi vào nhóm. Không mô tả cách xưng hô, không ghi chú, không phân tích, không đưa nhiều phương án.
6. Người thật có thể trả lời người vừa nói, hoặc mở chủ đề mới đang làm. Chọn điều chủ nhân có khả năng nhắn nhất.

=== CHAT ===
{context}
=== HẾT ===

Chỉ in ra đúng một tin nhắn của chủ nhân, không tiền tố, không dấu ngoặc:"""

BASE_LARK_PROMPT = """Dưới đây là đoạn chat công việc trên Lark giữa một người [CHỦ NHÂN] và đồng nghiệp.
Bạn không biết gì về người này ngoài đoạn chat.
Viết tin nhắn tiếp theo mà [CHỦ NHÂN] có khả năng nhất sẽ gõ. Bạn là người đó, không phải trợ lý.

=== CHAT ===
{context}
=== HẾT ===

Chỉ in ra tin nhắn, không tiền tố, không dấu ngoặc:"""

JUDGE_PROMPT = """Bạn là giám khảo. Có một đoạn hội thoại, câu THẬT người dùng đã gõ tiếp theo, và các câu ỨNG VIÊN do máy đoán.
Chấm từng ứng viên so với câu thật, mỗi tiêu chí 0-5:
- intent: cùng ý định và quyết định (đồng ý/từ chối/yêu cầu gì). Quan trọng nhất.
- facts: các chi tiết cụ thể (tên, số, việc) có đúng với câu thật không, có bịa thêm không.
- style: ngôn ngữ, độ dài, giọng, mức trang trọng giống câu thật không.
overall = 0.5*intent + 0.3*facts + 0.2*style.
Ứng viên được gán nhãn A/B ngẫu nhiên. Đừng đoán cái nào dùng brain.

=== HỘI THOẠI ===
{context}

=== CÂU THẬT ===
{actual}

{candidates}

Trả về DUY NHẤT một JSON, không markdown:
{{"scores": {{"A": {{"intent":0,"facts":0,"style":0,"overall":0,"note":"..."}}, "B": {{...}}}}}}"""


def cmd_persona_eval(n, model, judge_model, days_back, min_chars, seed, baseline, chat_glob, source="claude"):
    import random
    util.load_env()
    if not util.find_claude():
        sys.exit("!! cần claude CLI")
    if source == "lark":
        # Holdout: chỉ tin sau mốc T, chưa từng được ingest nên brain không thể thấy đáp án.
        cases = _pick_lark_cases(_lark_holdout_chats(), n, min_chars, seed)
        sim_prompt, base_prompt = SIM_LARK_PROMPT, BASE_LARK_PROMPT
    else:
        files = sorted((config.BASE / "raw" / "chats").glob(chat_glob))
        if not files:
            sys.exit("!! raw/chats trống. Chạy `chats --days N` trước.")
        cases = _pick_cases(files, n, min_chars, seed)
        sim_prompt, base_prompt = SIM_PROMPT, BASE_PROMPT
    if not cases:
        sys.exit("!! không tìm được lượt USER phù hợp")

    outdir = config.BASE / "eval" / PERSONA_DIR / f"{datetime.now():%Y-%m-%d-%H%M}"
    outdir.mkdir(parents=True, exist_ok=True)
    # Agent mô phỏng chạy trong bản sao chỉ chứa phần brain đã tinh luyện.
    # raw/, 00-inbox/, eval/, archive/, logs/, private/ không có mặt, nên không thể đọc đáp án hay token.
    cost, results = 0.0, []
    with claudecli._make_sandbox() as (sandbox, sim_settings):
        for i, c in enumerate(cases, 1):
            print(f"[{i}/{len(cases)}] {c['source']}", flush=True)
            brain_ans, k, ok1 = claudecli._claude_text(sim_prompt.format(context=c["context"]), model,
                                             "Read,Grep,Glob", sandbox, sim_settings)
            cost += k
            cands = {"brain": brain_ans}
            if not ok1:
                # Twin lỗi (timeout, thiếu CLI...): không gọi baseline, không đưa qua giám khảo, không chấm.
                results.append({**c, "answers": cands, "scores": {k2: None for k2 in cands}, "sim_ok": ok1})
                continue
            if baseline:
                base_ans, k, _ = claudecli._claude_text(base_prompt.format(context=c["context"]), model, "", sandbox)
                cost += k
                cands["baseline"] = base_ans
            keys = list(cands)
            random.Random(seed + i).shuffle(keys)
            label = {k2: chr(65 + j) for j, k2 in enumerate(keys)}
            cand_txt = "\n\n".join(f"=== ỨNG VIÊN {label[k2]} ===\n{cands[k2]}" for k2 in keys)
            raw, k, _ = claudecli._claude_text(JUDGE_PROMPT.format(context=c["context"], actual=c["actual"],
                                                         candidates=cand_txt), judge_model, "", sandbox)
            cost += k
            try:
                js = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])["scores"]
                scores = {k2: js[label[k2]] for k2 in keys}
            except Exception:
                scores = {k2: None for k2 in keys}
            results.append({**c, "answers": cands, "scores": scores, "sim_ok": ok1})

    def avg(key, field):
        vals = [r["scores"][key][field] for r in results if r["scores"].get(key)]
        return sum(vals) / len(vals) if vals else float("nan")

    (outdir / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    systems = ["brain"] + (["baseline"] if baseline else [])
    lines = [f"# Persona eval {datetime.now():%Y-%m-%d %H:%M}" + (" (Lark holdout sau mốc T)" if source == "lark" else ""),
             f"\n{len(results)} câu thật của chủ brain. Mô phỏng: {model}. Giám khảo: {judge_model}.",
             "Agent brain chạy trong bản sao chỉ có brain đã tinh luyện, không có raw/ hay inbox/. Agent baseline không biết gì về người dùng.",
             "Thư mục này không vào git vì chứa nguyên văn chat.\n",
             "| Hệ thống | intent | facts | style | overall /5 |", "|---|---|---|---|---|"]
    for s in systems:
        lines.append(f"| {s} | {avg(s, 'intent'):.2f} | {avg(s, 'facts'):.2f} | {avg(s, 'style'):.2f} | **{avg(s, 'overall'):.2f}** |")
    worst = sorted([r for r in results if r["scores"].get("brain")], key=lambda r: r["scores"]["brain"]["overall"])[:5]
    lines.append("\n## 5 câu brain đoán kém nhất\n")
    for r in worst:
        lines += [f"### {r['source']} — overall {r['scores']['brain']['overall']}",
                  f"- **Thật:** {r['actual'][:300]}", f"- **Brain:** {r['answers']['brain'][:300]}"]
        if baseline:
            lines.append(f"- **Baseline:** {r['answers']['baseline'][:300]}")
        lines += [f"- **Giám khảo:** {r['scores']['brain'].get('note', '')}", ""]
    lines.append("Brain thiếu gì để đoán đúng các câu trên? Bổ sung vào CRITICAL.md hoặc working-preferences.md.")
    (outdir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:9 + len(systems)]))
    print(f"\nreport: {outdir / 'report.md'}  est_usd={cost:.2f}")
    return 0
