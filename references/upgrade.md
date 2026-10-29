# Nâng cấp brain có sẵn theo khung mới

Dùng khi `brain.py locate` thấy máy đã có brain. Lệnh `upgrade` tự làm phần an toàn (ADD, UPDATE); file này
hướng dẫn phần MANUAL, cần phán đoán và hỏi người dùng. Không bao giờ xoá fact: bản cũ vào `archive/`.

## Ý nghĩa báo cáo `upgrade`

| Trạng thái | Nghĩa | Ai làm |
|---|---|---|
| OK | đã đúng khung | không cần |
| ADD | thiếu thư mục / file điều khiển / file khởi đầu / dòng .gitignore / mục INDEX | `--apply` tự thêm |
| UPDATE | file điều khiển (scripts, prompts, skill, README...) khác khung | `--apply` thay, bản cũ vào `private/upgrade-backup/<thời-điểm>/` |
| SKIP | như UPDATE nhưng chạy với `--skip-update` nên giữ nguyên | không |
| MANUAL | cần Claude làm cùng người dùng | theo các mục dưới |
| NOTE | cấu hình máy nên làm (lịch job, collect, MCP) | Bước 4 và 6c của SKILL.md |

Trước khi `--apply` với UPDATE: xem file nào người dùng đã sửa riêng (`diff <brain>/<file> <khung>/<file>`).
Có phần riêng (prompt thêm nguồn dữ liệu, README thêm mục) thì hỏi: thay rồi gộp lại phần riêng từ bản backup,
hay chạy `--skip-update`. Brain chứa chính skill này (khung được chép ra từ nó) luôn dùng `--skip-update`.

## MANUAL: AGENTS.md

`upgrade` không ghi đè AGENTS.md vì nó có Lessons và luật riêng của người dùng. Mở bản khung
(`assets/template/AGENTS.md`), thêm vào brain các mục và câu còn thiếu theo báo cáo, giữ nguyên phần riêng.
Thay `{{NAME}}`, `{{OWNER}}`, `{{DATE}}` bằng giá trị thật. Những mục hay thiếu ở brain cũ:
- Thư mục: format dashboard `20-projects/`, `25-areas/`, `50-knowledge/rules/` (luật có `ack`).
- `## Việc được tự làm và việc phải hỏi` (rào quyền).
- Không chép thông tin brain sang repo khác, dùng `/dispatch`, không ghi key vào vault.

## MANUAL: 20-projects/ chưa ở dạng dashboard

Với mỗi file trong báo cáo:
1. Copy nguyên bản vào `archive/<tên>-<YYYY-MM>.md`, thêm `invalid_at: <hôm nay>` và
   `superseded_by: 20-projects/<tên>.md (format dashboard)` vào frontmatter.
2. Tìm repo của dự án trên máy (`find ~ -maxdepth 3 -type d -name '<tên>*'`), ngày hoạt động gần nhất
   (`git -C <repo> log -1 --format=%ad --date=short`).
3. Viết lại dashboard: frontmatter thêm `status` (active nếu hoạt động trong 14 ngày hoặc có trong
   CRITICAL.md, idle nếu quá, done nếu người dùng nói xong), `area`, `repo`, `last_activity`; thân đúng 5 mục
   `## Trạng thái` / `## Đang treo` / `## Next steps` / `## Quyết định` / `## Xem thêm`. Mục trống ghi
   "Không có trong brain". Next steps chỉ ghi việc người dùng đã nói.
4. Chi tiết kỹ thuật có trong repo: bỏ, chỉ giữ `repo:`. Nghiệp vụ không repo nào giữ (vd từ chat Lark,
   họp): chuyển nguyên văn sang `50-knowledge/<dự-án>-<chủ-đề>.md`, dashboard link sang ở `## Xem thêm`.
5. Giữ nhãn nguồn và "as of" của từng fact. Fact mới lấy từ git thì nguồn `git`.

## MANUAL: 25-areas/ trống

Hỏi người dùng 1–4 mảng trách nhiệm dài hạn (gợi ý từ các dự án đang có và CRITICAL.md). Mỗi mảng một file
`25-areas/area-<slug>.md` (format ở SKILL.md Bước 3), mục `## Dự án` liệt kê dashboard thuộc mảng đó, rồi
thêm `area: area-<slug>` vào frontmatter từng dashboard. Tiêu chuẩn chung cho cả mảng (cách deploy, môi trường,
luật dùng chung) chuyển từ các dashboard lên `## Tiêu chuẩn cần giữ` của area.

## MANUAL: luật còn dạng 1 dòng

Mỗi dòng trong `## Luật làm việc` của `working-preferences.md` chưa phải `- [[rule-...]]` thành một file
`50-knowledge/rules/rule-<slug>.md` (format ở `prompts/ingest.md` mục 4): Luật / Why / How to apply (có cả
khi KHÔNG áp dụng) / Bằng chứng, `ack: false`. Tìm câu nguyên văn trong file nguồn ghi ở dòng luật (thường
trong `raw/chats/` hoặc `00-inbox/done/`) để viết Why. Không tìm được lý do thì ghi
"(suy luận, chờ xác nhận)". Rồi thay dòng cũ bằng index `- [[rule-<slug>]] — <luật 1 dòng> — khi: <ngữ cảnh>`.

## Kết thúc

1. Cập nhật INDEX.md cho mọi file mới hoặc đổi (dashboard, area, rule, knowledge, archive), append LOG.md.
2. `PY scripts/brain.py doctor`, rồi `PY scripts/brain.py run lint`: dòng cuối `logs/run.log` phải `ok=True`
   và báo cáo lint không còn lỗi format dashboard / rule.
3. Lịch job: nếu báo thiếu job thì `schedule install --jobs collect,ingest,reflect,lint,sync,prune`
   (chỉ thêm `sync` nếu máy này vốn chạy sync).
4. Hỏi người dùng trước khi commit và push. Commit không có trailer ghi công AI.

## Chuyển từ second-brain-lite (hoặc vault markdown khác)

`upgrade` chỉ dùng cho brain cùng cấu trúc. Brain dựng bằng skill `second-brain-lite` (thư mục `memory/`, `0-inbox`..`4-archive`,
có `.brain-version`) khác cấu trúc, nên chuyển dữ liệu sang một brain đích bằng `brain.py migrate <nguồn> [--apply]`.
`locate` liệt kê brain lite trên máy. Nguồn chỉ đọc; mặc định dry-run; không ghi đè file có sẵn; mỗi file tạo ra có
`migrated_from: <tên nguồn>:<đường dẫn>` nên chạy lại chỉ ra SKIP.

| Nguồn (lite) | Đích (brain này) |
|---|---|
| `memory/nguoi-dung.md`, `memory/uu-tien-hien-tai.md` | `CRITICAL.md` (chỉ điền dòng còn `(chưa điền)`, khác thì MANUAL) |
| `memory/*` type `feedback` | `50-knowledge/rules/rule-<slug>.md` (Luật/Why/How to apply/Bằng chứng, giữ `ack` và `applies_to`) + 1 dòng index trong `working-preferences.md` |
| `memory/*` type `user` / `project` | `50-knowledge/<slug>.md` |
| `memory/*` type `reference` tên `nguoi-*` | 1 dòng trong `30-people/team-map.md` (chỉ vai trò, cách làm việc) |
| `memory/*` type `reference` khác | `90-reference/<slug>.md` |
| `1-projects/<x>/_dashboard.md` | `20-projects/<x>.md` (5 mục, `status`, `area: area-<slug>`, `repo` hoặc `none`, `last_activity`, `due`) |
| `1-projects/<x>/*.md` khác | `50-knowledge/<x>-<tên>.md`, dashboard link ở `## Xem thêm` |
| `4-archive/<x>/_dashboard.md` | `20-projects/<x>.md` với `status: done` (không chuyển file theo luật của brain này) |
| `2-areas/<x>.md` | `25-areas/area-<x>.md` (Mục tiêu/tiêu chuẩn → Tiêu chuẩn cần giữ, Dự án liệt kê dashboard). Dự án không có area → `area-general` |
| `3-resources/*.md` | `50-knowledge/<slug>.md` |
| `4-archive/luat-da-bo/*`, file lưu trữ khác | `archive/` (luật đã bỏ có `invalid_at`) |
| `0-inbox/luat-*.md` (luật ứng viên) | 1 dòng chờ duyệt trong `eval/review-queue.md` kèm bằng chứng nguyên văn |
| `0-inbox/nguon-*.md`, file `.md` ngoài cấu trúc lite | `00-inbox/local/import-<nguồn>-*.md`, bọc `<untrusted>`, nhãn `USER-PASTED`, chờ ingest |
| `0-inbox/de-xuat-*`, `tong-ket-tuan-*`, `goi-y-skill` | bỏ qua (job lite tự sinh từ nguồn đã chuyển) |
| `private/`, `logs/`, `scripts/`, `.brain-jobs/`, `.claude/` | không đọc, không chuyển |

Thư mục markdown không phải lite (vd vault Obsidian): mọi file `.md` (trừ `.obsidian/`, `.trash/`, `private/`...) vào
`00-inbox/local/` để ingest trích fact theo luật thường. Nguồn cùng cấu trúc brain này thì từ chối: gộp bằng git.

Mọi nội dung chép sang qua `redact()` (che key/token). `[[link]]` tới memory cũ được đổi sang tên file mới; link không
tìm thấy thì bỏ ngoặc để `check` không báo link chết. Sau `--apply`: `check`, rồi `run ingest` cho file inbox.
