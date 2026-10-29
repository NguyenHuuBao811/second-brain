# {{NAME}}

Second brain dạng markdown cho Claude Code và mọi AI agent (Codex, Gemini CLI, Cursor...). Chạy trên macOS, Ubuntu và Windows.
Mọi lệnh đều qua `scripts/brain.py`. Trên Windows thay `python3` bằng `py -3`.

## Hằng ngày

- **Nạp dữ liệu:** job `collect` mỗi tối tự gom chat Claude Code và commit git mới của các dự án bạn cho phép (`collect --allow`) vào `00-inbox/local/`. Thư mục này không vào git và bí mật được che trước khi ghi. Muốn nạp thêm tài liệu khác, bỏ file `.md` vào đó. Job ingest chạy mỗi giờ sẽ trích fact vào brain.
- **Hỏi:** mở Claude Code trong thư mục này và hỏi bình thường, hoặc dùng `/query`.
- **Mỗi tuần 10 phút:** đọc `eval/review-queue.md` và `10-daily/`, sửa fact sai.
  Mở báo cáo lint mới nhất (`eval/lint-*.md`): duyệt luật `ack: false` trong `50-knowledge/rules/` (đúng thì đổi `ack: true`, sai thì sửa hoặc xoá).
  Agent làm sai mà bạn sửa: bảo nó "ghi thành luật". Đây là nguồn huấn luyện quý nhất.

## Cấu trúc

| Thư mục | Chứa gì |
|---|---|
| `00-inbox/` | Chỗ đổ tạm, ingest đọc rồi chuyển vào `done/` |
| `10-daily/` | Nhật ký ingest theo ngày |
| `20-projects/` | 1 dashboard/dự án, cùng format: `status`, `area`, `repo`, `last_activity` + 5 mục Trạng thái / Đang treo / Next steps / Quyết định / Xem thêm |
| `25-areas/` | 1 file/mảng trách nhiệm dài hạn (PARA): phạm vi, tiêu chuẩn cần giữ, dự án con |
| `30-people/` | Công ty, `team-map.md` (ai giữ việc gì) |
| `40-decisions/` | 1 file/quyết định: What / Why / Date / Status |
| `50-knowledge/` | Kiến thức; `working-preferences.md` là giọng viết + index luật |
| `50-knowledge/rules/` | 1 file/luật làm việc: Luật / Why / How to apply / Bằng chứng, `ack: false` tới khi bạn duyệt |
| `archive/` | Bản cũ đã bị thay (`invalid_at`) |
| `raw/`, `private/` | Nguồn gốc không sửa; bí mật không vào git |

Tài liệu dự án (spec, kiến trúc) để trong repo của dự án. Brain chỉ giữ trạng thái, quyết định, luật làm việc và nghiệp vụ không repo nào giữ.

## Lệnh

| Lệnh | Việc |
|---|---|
| `run ingest` | Nạp file trong `00-inbox/` vào brain |
| `run reflect` | Gộp và dọn brain hằng tuần |
| `run lint` | Báo file lỗi, link gãy, file cũ (chạy `check` tất định trước, rồi model đọc phần cần hiểu) |
| `check [--backfill] [--json]` | Kiểm tất định, không gọi model: mồ côi, link chết, thiếu `related`/frontmatter, stale theo `last_verified`, file > 200 dòng, INDEX lệch, mâu thuẫn, qa quá hạn, hub thiếu backlink. Mã thoát 1 khi có lỗi chặn. `--backfill` thêm `last_verified = updated` cho file cũ |
| `gaps [--days 7] [--write]` | Câu hỏi brain chưa trả lời được (từ `logs/hoi-dap.jsonl`) + dự án có mục "Không có trong brain" |
| `search <từ>` | Tìm BM25 (SQLite FTS5, index ngoài git ở `~/.cache/hibrain/index.db`, đổi bằng `BRAIN_INDEX_DB`); máy không có FTS5 thì grep |
| `index --build [--dry]` / `index <mảng>` | Tách INDEX lõi (< 17KB) + `indexes/index-<mảng>.md`; in chỉ mục con một mảng |
| `conflicts [--apply]` | Fact cùng đối tượng + thuộc tính mà giá trị khác; `--apply` ghi mục Mâu thuẫn của `eval/review-queue.md` |
| `qa find <câu>` / `qa prune [--apply]` | Câu trả lời đã lưu ở `50-knowledge/qa/` (có hạn dùng, nguồn đổi thì kiểm lại) |
| `hub new <person\|project\|system> <tên>` / `hub sync` | Trang trung tâm `50-knowledge/hubs/`; sync viết backlinks trong Xem thêm |
| `verify-sample [--n 10] [--dry]` | Agent khác (`BRAIN_VERIFY_MODEL`, mặc định opus) đối chiếu N fact có mã nguồn với bản gốc, fact sai vào review-queue. Trần 1 USD, job tuần `verify` |
| `eval [--dry] [--n N] [--budget 2]` | Câu hỏi vàng tất định: hit/đúng/thời gian/token mỗi câu → `logs/eval-<ngày>.jsonl`, `eval/results-auto-<ngày>.md` |
| `reingest <raw_id> \| --since DATE [--apply]` / `raw-prune [--apply]` | Chạy lại ingest từ kho bản gốc ngoài git (`BRAIN_RAW_ARCHIVE`, giữ `BRAIN_RAW_KEEP_DAYS`=180 ngày). Mặc định dry-run |
| `run eval` | Chấm điểm brain theo `eval/golden.jsonl` (+ `eval/golden-lark.jsonl` nếu có) |
| `run prune` | Dọn fact tiến độ quá 14 ngày, quyết định bị đè, luật trùng/mâu thuẫn, review-queue cũ |
| `persona-eval` | Đo brain mô phỏng chủ brain giống tới đâu (`--help` xem tuỳ chọn) |
| `chats --days 7` | Chuyển chat Claude Code thật của máy này sang `raw/chats/` |
| `git <repo>` | Chuyển lịch sử git của một repo sang `raw/git/` |
| `lark chats` / `lark collect` | (Tuỳ chọn) kéo chat Lark trong allowlist `private/lark-chats.txt` vào `00-inbox/local/lark/`, cần `lark-cli` đã login |
| `lark send --chat <nhóm> [--text T \| --text-file F] [--file P] [--send]` | Bot (Lark app, key ở `private/lark-bot.env`) gửi tin/file vào nhóm bot đang ở. Mặc định dry-run; chặn nội dung có key |
| `collect` | Gom chat Claude Code và commit git mới của dự án được phép vào `00-inbox/local/` |
| `collect --allow <dir>` | Cho phép gom một dự án. `--disallow`, `--list` để bỏ và xem |
| `sync` | Đẩy inbox lên, kéo brain mới về |
| `history [--limit 20]` / `restore <số>` | Các lần lưu. Có git: `git log` (hoàn tác bằng `git revert`). Không git: bản chụp `logs/snapshots/`, `restore` đưa dữ liệu về bản đó (tự chụp bản hiện tại trước) |
| `locate` | Liệt kê brain đã có trên máy |
| `upgrade <brain> --template <khung> [--apply] [--skip-update]` | So brain có sẵn với khung skill, bổ sung phần thiếu (không đụng dữ liệu) |
| `migrate <thư-mục> [--apply]` | Chuyển dữ liệu từ brain cấu trúc khác vào brain này: second-brain-lite (memory → luật/CRITICAL/30-people/50-knowledge, 1-projects → dashboard, 2-areas → 25-areas, 3-resources → 50-knowledge, 4-archive → archive) hoặc thư mục `.md` bất kỳ (vào `00-inbox/local/` chờ ingest). Nguồn chỉ đọc, mặc định dry-run, không ghi đè, chạy lại không nhân bản |
| `status` / `commit -m MSG FILE...` | `git status` + diff của brain; commit đúng các file dữ liệu đã kể (chặn file điều khiển) |
| `dispatch <dự-án> "<việc>" [--edit] [--allow T]` | Giao việc cho agent chạy trong repo của dự án (repo lấy từ dashboard). Mặc định chỉ lập kế hoạch; `--edit` cho sửa + commit trên branch mới; không bao giờ push/deploy. Log ở `logs/dispatch/` |
| `doctor` | Kiểm tra máy |
| `register` | Ghi máy này vào `machines.md` |
| `context` / `search <từ khoá>` / `read <path>` | Cho agent không có MCP đọc brain |
| `capture --title T --agent A` | Agent gửi ghi chú (stdin) vào `00-inbox/` |
| `mcp-config` | In cấu hình MCP cho Claude Code, Codex, Gemini CLI, Cursor |
| `schedule install / status / uninstall` | Bật, xem, tắt job nền |

## Không có git

Brain tạo bằng `init --no-git` (hoặc máy chưa cài git) vẫn chạy đủ: mỗi lần job hoặc `commit` lưu là một bản chụp `.zip`
phần dữ liệu trong `logs/snapshots/` (giữ 90 bản) + một dòng nhật ký `logs/nap.jsonl`. Xem `history`, quay lại `restore <số>`.
Không đồng bộ nhiều máy, không sao lưu lên mạng. Cài git sau: `git init && git add -A && git commit -m "init"` trong brain.

## Nhiều máy

Mọi máy đều ghi được (collect, ingest, reflect, lint, sync, prune), đồng bộ qua một git remote private.
`machines.md` liệt kê các máy đã đăng ký. Chống xung đột:
- lịch job mỗi máy lệch thêm một số phút cố định theo tên máy;
- `git pull --rebase` lỗi thì thử lại với `-X theirs` (phần trùng giữ bản của máy đang ghi);
- `reflect`, `lint`, `prune` chỉ một máy chạy mỗi kỳ, máy khác thấy commit thì bỏ qua (`run <job> --force` để ép);
- `00-inbox/` dùng chung: file máy nào đẩy lên thì máy đó ingest, quá 3 giờ chưa ai nạp thì máy nào cũng nhận. `00-inbox/local/` riêng từng máy.

Cài trên máy mới (giống máy đầu):

```bash
git clone <remote-url> && cd <thư-mục>
claude setup-token && python3 scripts/brain.py set-token   # tuỳ chọn: chỉ khi job nền báo lỗi đăng nhập (hay gặp trên macOS)
python3 scripts/brain.py register
python3 scripts/brain.py schedule install --jobs collect,ingest,reflect,lint,sync,prune,verify
python3 scripts/brain.py doctor
```

## Dùng với agent khác

Hướng dẫn chung ở `AGENTS.md`; `CLAUDE.md` và `GEMINI.md` chỉ trỏ về đó.
Agent có MCP dùng `scripts/brain_mcp.py` (tool `brain_context`, `brain_search`, `brain_read`, `brain_capture`);
`python3 scripts/brain.py mcp-config` in cấu hình sẵn. Agent không có MCP dùng `context`, `search`, `read`, `capture`.
Ghi chú từ agent vào `00-inbox/`, ingest coi là lời trợ lý cần xác nhận. Job nền vẫn chạy bằng Claude Code CLI.

## Lịch mặc định

| Job | Lịch | Model |
|---|---|---|
| collect | 23:47 hằng ngày | không dùng Claude |
| ingest | mỗi giờ, phút 07 | sonnet |
| sync | mỗi giờ, phút 37 | không dùng Claude |
| lint | 06:13 hằng ngày | haiku |
| reflect | Chủ nhật 20:03 | sonnet |
| prune | Thứ bảy 21:03 | sonnet |
| verify | Chủ nhật 05:41 | `BRAIN_VERIFY_MODEL` (mặc định opus), trần 1 USD |

Không nằm trong `--jobs` mặc định. `lark` cần `lark-cli` đã đăng nhập user. `learn` và `learn-day` cần bot Lark đầy đủ
(`scripts/lark_bot.py` + `scripts/hibrain/lark_bot/`, có lệnh duyệt `hoc`), khung này chưa kèm bot đó:

| Job | Lịch | Model |
|---|---|---|
| lark | 22:53 hằng ngày, kéo chat Lark trong allowlist | không dùng Claude |
| learn | mỗi giờ, phút 27: học từ lời chủ brain + web (`50-knowledge/learn-topics.md`) | sonnet |
| learn-day | 17:45 đúng giờ, DM tổng hợp cả ngày + danh sách chờ duyệt | sonnet |

Luật và kiến thức web do learn ghi nằm ở `00-inbox/learn-pending/` tới khi chủ brain duyệt qua DM bot
(`hoc`, `hoc duyet <id|het>`, `hoc bo <id|het>`). Bot dựng bằng skill `lark-brain-bot` chưa có lệnh này: đừng cài
learn/learn-day, vì mục học được sẽ nằm chờ mãi, không có nút hay lệnh nào để duyệt.

Phút là mốc gốc; mỗi máy cộng thêm độ lệch riêng theo tên máy.
Mọi lần gọi Claude chạy bằng tài khoản Claude trước; hết quota thì chạy lại qua gateway nếu có
(`HIBRAIN_GATEWAY_ANTHROPIC_*` trong `private/claude.env`, không có thì `env` của `~/.claude/settings.json`; tắt: `HIBRAIN_GATEWAY=0`).

Công tắc: `BRAIN_CRITIC=0` tắt bước phản biện câu phức tạp (log `logs/critic.jsonl`); `BRAIN_ROLES=1` tách vai ingest
(trích `BRAIN_MODEL_EXTRACT`=haiku → thủ thư `BRAIN_MODEL_LIBRARIAN` → kiểm `BRAIN_MODEL_VERIFY`, prompt `prompts/role-*.md`);
`BRAIN_FTS=0` dùng grep thay BM25.
Job nền dùng hạn mức của gói Claude subscription, không tính tiền API.
Log ở `logs/run.log`.

## An toàn

Nội dung inbox đến từ chat và tài liệu, có thể chứa lệnh cài cắm. Vì vậy job nền:
- không có Bash, chỉ ghi được vào thư mục dữ liệu;
- bị `headless/settings.json` chặn sửa `scripts/`, `prompts/`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`;
- chỉ commit dữ liệu, file điều khiển bị đổi thì ghi cảnh báo vào log.

Agent làm việc trong brain theo luật "việc được tự làm và việc phải hỏi" ở `AGENTS.md`: revert được thì tự làm, không revert được (push/merge prod, gửi tin cho người khác, xoá dữ liệu ngoài git) thì hỏi trước.
