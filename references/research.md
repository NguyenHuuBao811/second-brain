---
type: reference
title: Research - Second brain cho AI agent
description: Tổng hợp 3 báo cáo research (cấu trúc, vòng huấn luyện, bootstrap+eval) ngày 2026-10-10
updated: 2026-10-10
---

# 1. Cấu trúc khuyến nghị

Kết luận chính: thứ quyết định hiệu quả không phải tên thư mục mà là **lớp định tuyến** (AGENTS.md + INDEX.md; CLAUDE.md/GEMINI.md chỉ trỏ về AGENTS.md), **one home per topic**, và **frontmatter description**. Mô hình "ceo-brain" là Johnny-Decimal lite, ổn nhưng nên gộp bớt thư mục.

| Mô hình | Mạnh cho agent | Yếu cho agent |
|---|---|---|
| PARA | Ít thư mục, Archive giảm nhiễu | Note đổi chỗ theo thời gian, link gãy, không có index |
| Zettelkasten | Note nhỏ = ít token, retrieval chính xác | Cần search tool, agent dễ tạo note trùng |
| Johnny Decimal | Path ổn định, `ls` là index, dễ grep | Số không mang nghĩa cho LLM nếu thiếu mô tả |
| MOC + Karpathy LLM-wiki | Đọc 1 index rồi nhảy đúng trang, token cố định thấp | Phải duy trì index mỗi lần ghi |

```
brain/
├── AGENTS.md        # <100 dòng: luật đọc/ghi, "đọc INDEX trước" (CLAUDE.md trỏ về)
├── INDEX.md         # 1 dòng/file: path — mô tả — updated (≤200 dòng)
├── CRITICAL.md      # ~150 token: tôi là ai, ưu tiên hiện tại, luôn nạp
├── LOG.md           # append-only, 1 dòng/lần ghi
├── 00-inbox/        # thô, agent chỉ đọc khi "ingest"
├── 10-daily/        # audit trail, không phải kho fact
├── 20-projects/     # 1 file/dự án: trạng thái, next, link quyết định
├── 30-people/       # người + công ty
├── 40-decisions/    # What / Why / Date
├── 50-knowledge/    # concept nguyên tử, cross-link
├── 90-reference/    # tĩnh, ít đổi
├── raw/             # nguồn gốc bất biến
├── eval/            # golden.jsonl + results
├── scripts/         # lint, digest, consolidate
├── .claude/skills/  # /ingest /query /lint /eval
└── private/         # gitignore
```

Frontmatter bắt buộc: `type, title, description, updated`; tuỳ chọn `tags, confidence, related`. Quy tắc: one home per topic, newest wins; tên file lowercase-hyphen duy nhất; mỗi claim có "as of YYYY-MM"; note <200 dòng.

Token: boot chỉ đọc AGENTS.md + CRITICAL.md + INDEX.md (progressive disclosure 3 tầng). >200 file thì thêm keyword search (FTS) trước khi nghĩ tới embedding.

# 2. Vòng huấn luyện

Kiến trúc 2 tầng hội tụ từ Mem0, Zep, Letta, Generative Agents: **extract khi ghi** + **consolidate ngoài giờ**.

| Bước | Tần suất | Việc |
|---|---|---|
| A. Extract | mỗi giờ (cron) | Đọc inbox → xuất fact theo schema vào buffer, chưa sửa vault |
| B. Daily consolidate | 1/ngày, Haiku | Mỗi fact: tìm fact tương tự → ADD / UPDATE / INVALIDATE / NOOP. Không xoá, set `invalid_at` |
| C. Weekly reflect | 1/tuần | 3-5 câu hỏi cấp cao → insight mới, gộp topic, đẩy cũ sang archive |
| D. Human review | 10 phút/tuần | Duyệt review-queue (confidence <0.7, mâu thuẫn). Mỗi lần sửa → 1 dòng lessons.md |
| E. Rebuild index | sau mỗi consolidate | INDEX ≤200 dòng |

Schema fact:
```yaml
id, subject, predicate, object, text (câu tự đủ nghĩa)
type: user|feedback|project|reference|decision
source, observed_at, valid_at, invalid_at, superseded_by
confidence (<0.5 không xuất), tags, review: pending|approved
```

Headless:
```bash
claude -p "$(cat prompts/consolidate.md)" --model haiku --max-turns 15 \
  --max-budget-usd 2 --permission-mode dontAsk \
  --allowedTools "Read,Grep,Glob,Edit,Write" --output-format json
```

5 pitfalls: (1) consolidate phá kiến thức đúng → giữ fact gốc trong archive, chỉ gộp tóm tắt; (2) over-merge → chỉ merge cùng subject+predicate, ≤3 fact/lần; (3) mâu thuẫn ngang hàng → recency-wins + invalid_at tường minh; (4) loop/cost → max-turns, max-budget, timeout, lock file; (5) 2 nguồn ghi 1 file → cron commit git mỗi lần, review bằng diff.

# 3. Bootstrap 7 ngày

| Ngày | Việc |
|---|---|
| 1 | Dựng khung (có thể clone llm-wikid) |
| 2 | Export Claude/ChatGPT chat + git log → md (nguồn đậm quyết định nhất) |
| 3 | Ingest batch 1 (20-40 file/lần), Haiku extract song song, model mạnh merge |
| 4 | Slack (slack2md) + Gmail (mbox-md), lọc channel/label quan trọng |
| 5 | Notion/Drive qua markitdown hoặc MCP; Calendar chỉ lấy recurring + attendees |
| 6 | Viết golden Q&A 30-50 câu, chạy eval baseline, lint |
| 7 | Fix gap, gắn MCP feed liên tục, đặt cron ingest hằng ngày |

Ước lượng: ngày 1 hỏi đáp cơ bản được; tuần 1 phủ 70-80% câu thường gặp; tháng 1 mới có lint/staleness ổn định.

Tool: claude-conversation-exporter, ChatGPT_Conversations_To_Markdown, slack2md, mbox-md, markitdown, gitstory, llm-wikid, agent-memory-vault, obsidian-mcp-for-claude-code.

# 4. Eval

| Metric | Cách đo |
|---|---|
| Hit@k | câu golden ghi page kỳ vọng, agent cite đúng không |
| Faithfulness | Claude-judge: claim có nằm trong page cite |
| Correctness | so ground truth 0-1 |
| Needle | chèn 5 fact giả, ingest, hỏi lại |
| Staleness | % page không sửa >90 ngày |
| Lint | orphan, broken link, mâu thuẫn |

`/wiki-eval`: với mỗi q trong eval/golden.jsonl → trả lời chỉ dùng vault → subagent chấm → commit eval/results-YYYYMMDD.md.

# Nguồn
- https://aaif.io/blog/karpathys-llm-wiki-as-agent-memory
- https://github.com/binteca/second-brain
- https://github.com/eliferres/agent-memory-vault
- https://www.humanlayer.dev/blog/writing-a-good-claude-md
- https://umesh-malik.com/blog/ai-agent-knowledge-base-architecture
- https://agentskills.io/specification
- https://arxiv.org/html/2504.19413v1 (Mem0)
- https://www.getzep.com/blog/beyond-static-knowledge-graphs/
- https://forum.letta.com/t/sleeptime-agents-for-memory-consolidation-best-practices-guide/154
- https://code.claude.com/docs/en/memory
- https://hindsight.vectorize.io/blog/2026/05/21/agent-memory-consolidation
- https://arxiv.org/pdf/2605.12978
- https://www.mindstudio.ai/blog/karpathy-llm-wiki-pattern-cut-claude-token-usage-95-percent
- https://github.com/shannhk/llm-wikid
- https://platform.claude.com/cookbook/capabilities-knowledge-graph-guide
- https://langfuse.com/resources/engineering/evaluation-of-rag-with-ragas
- https://sierra.ai/uk/blog/evaluating-and-improving-search
