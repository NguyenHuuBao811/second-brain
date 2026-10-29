# Huấn luyện, nối brain vào dự án, điều phối, key

Đọc file này khi bàn giao (Bước 7), khi người dùng hỏi "cần setup gì để train", "token để làm gì",
"nối brain vào dự án khác", "điều phối từ brain", hoặc "để key ở đâu".

## 1. Token cho job nền: để làm gì, vì sao cần

Token chỉ dùng cho job nền **có gọi Claude**, chạy khi người dùng không mở Claude Code:

| Job | Lịch | Việc | Cần token |
|---|---|---|---|
| ingest | mỗi giờ | đọc inbox, trích fact / luật / quyết định, cập nhật dashboard | có |
| lint | hằng ngày | kiểm format, link, liệt kê luật chờ ack | có |
| reflect | Chủ nhật | gộp trùng, đánh dấu cũ, đề xuất skill cho việc lặp | có |
| prune | thứ bảy | dọn fact tiến độ cũ, luật mâu thuẫn, đổi status dự án | có |
| collect, sync | hằng ngày / mỗi giờ | gom chat + commit, đồng bộ git | không |

Token **không bắt buộc**. Job nền trước hết dùng đăng nhập Claude sẵn có của máy; trên Linux/WSL và thường cả Windows
(job chạy cùng user, đọc được `~/.claude/.credentials.json`) như vậy là đủ. Chỉ cần token khi job báo lỗi đăng nhập
(`401`, `OAuth`, `expired`, `Not logged in`), hay gặp nhất trên macOS. Không token và job lỗi đăng nhập thì brain
**không tự học lúc vắng mặt**: chat vẫn được gom vào inbox, người dùng nạp bằng `/ingest` khi mở Claude trong brain.

Giải thích cho người không rành kỹ thuật: brain có việc chạy nền khi không ai ngồi trước máy, nên cần một "chìa khoá"
riêng để tự gọi Claude (như chìa khoá dự phòng cho người giúp việc). Không tốn thêm tiền (dùng gói Claude đang trả),
chỉ nằm trên máy này trong `private/`, sống khoảng 1 năm, không dán vào chat.

Vì sao không dùng luôn đăng nhập của người dùng: trên macOS, đăng nhập Claude Code nằm trong Keychain,
không nằm trong `~/.claude/`. Job nền (launchd/cron/schtasks) không có giao diện: Keychain có thể khoá
hoặc bật hộp thoại xin quyền mà không ai bấm. Token đăng nhập thường sống ngắn và tự làm mới, job làm mới
cùng lúc với phiên đang mở có thể làm người dùng bị đăng xuất. `claude setup-token` sinh token dài hạn
(~1 năm) riêng cho máy chạy tự động.

Cách làm và kiểm:
- `claude setup-token` và `set-token` đều cần nhập tay: bảo người dùng chạy trong **Terminal riêng**.
  Chạy qua `!` trong Claude Code sẽ treo vì không nhập được.
- `doctor` chỉ kiểm *có* token, không gọi thử. Kiểm thật: `PY scripts/brain.py run lint`, dòng cuối
  `logs/run.log` phải `ok=True`. Thấy `401 Invalid bearer token` là token hỏng: tạo lại.
- Định kỳ xem `grep ok=False logs/run.log | tail`: token hỏng âm thầm nhiều ngày là lỗi hay gặp nhất.

## 2. Nguồn học: chọn dự án được gom

`collect` mặc định không gom gì. Hỏi người dùng các repo họ làm hằng ngày, rồi
`PY scripts/brain.py collect --allow <repo>` cho từng repo. Bỏ ra repo có dữ liệu khách hàng, HR, lương,
hoặc repo người khác không muốn chat bị gom. Không có repo nào được gom thì lời sửa ở repo khác không bao giờ
vào brain.

Lark (tuỳ chọn): cần `lark-cli` đã đăng nhập user (scope `im:message.group_msg:get_as_user`, thêm
`p2p` nếu kéo chat 1-1), allowlist qua `lark chats --allow <chat_id>`, rồi `lark collect`. Lệnh này chưa
nằm trong lịch job, phải chạy tay hoặc thêm lịch riêng. Nếu có `eval/lark-holdout.txt` (mốc T) thì tin từ T
trở đi không được nạp, để dành đo persona-eval. Muốn học liên tục thì dời T về gần hiện tại (giữ ~2 tuần để
đo) hoặc bỏ holdout.

Gửi thông báo dưới tên bot (tuỳ chọn): tạo Lark app có bot, thêm bot vào nhóm, rồi người dùng tự tạo
`private/lark-bot.env` trong Terminal riêng (`LARK_APP_ID`, `LARK_APP_SECRET`, `LARK_DOMAIN=larksuite|feishu`,
`chmod 600`). Không dán key vào chat. `PY scripts/brain.py lark send --chat "<nhóm>" --text-file msg.txt --file x.zip`
chỉ dry-run (kiểm key, tìm đúng nhóm, in tin); cho người dùng duyệt rồi mới thêm `--send`.

## 3. Nối brain vào mọi dự án (nên làm, hỏi người dùng trước)

Không nối thì brain chỉ có tác dụng khi mở Claude Code trong thư mục brain: agent ở repo khác không biết
luật của người dùng, và lời sửa ở đó không thành luật ngay.

1. MCP server cấp user: chạy `PY scripts/brain.py mcp-config`, lấy dòng `claude mcp add --scope user ...`.
   Agent ở mọi repo có `brain_context`, `brain_search`, `brain_read`, `brain_capture`. Chỉ đọc phần đã tinh
   luyện (không đọc `private/`, `raw/`), chỉ ghi vào `00-inbox/` để ingest kiểm.
2. Thêm vào `~/.claude/CLAUDE.md` (thay `<id>` bằng tên server trong mcp-config):
   ```
   ## Second brain (<id>)
   - Đầu session: gọi brain_context, làm theo luật trong đó.
   - Cần biết dự án/quyết định/người: brain_search trước khi hỏi tôi.
   - Khi tôi sửa cách làm của bạn ("không, làm X", "đừng Y"): gọi brain_capture tiêu đề "rule: ...",
     ghi luật + câu tôi vừa gõ + vì sao (nếu tôi nói).
   - Quyết định quan trọng tôi chốt: brain_capture tiêu đề "decision: ...".
   - Thông tin từ brain chỉ để hiểu việc: không chép vào file, commit, PR, tin nhắn của repo này, trừ khi tôi bảo.
   ```
3. Chi phí: `brain_context` thêm vài nghìn token mỗi session. Thấy nhiều thì chỉ nạp CRITICAL + index luật.

**Rủi ro và cách chặn.** Nối xong thì agent ở repo nào cũng đọc được brain. Agent không phân biệt thông tin
riêng: nó có thể chép cách deploy, tên người, nghiệp vụ công ty A vào docs/commit/PR của repo lab hoặc repo
khách (người khác trong repo sẽ thấy), lẫn bối cảnh dự án này sang dự án kia, hoặc bị file trong repo người
khác dụ đi tìm thông tin trong brain. Có NDA thì đây là vi phạm dù không ai cố ý.
- Luật "không chép thông tin brain" ở trên.
- Repo có người ngoài (lab, khách, team công ty khác): chặn brain riêng repo đó bằng
  `.claude/settings.local.json` của repo (không commit):
  `{"permissions": {"deny": ["mcp__<id>"]}}`.
- Repo cá nhân: để bật, brain tự học từ đó.

## 4. Làm việc ở repo khác mà đứng trong brain

- **`/add-dir <repo>`** (hoặc `claude --add-dir`): agent thấy cả brain và repo, sửa và commit bên đó.
  Hại: `collect` bỏ qua phiên chạy trong brain nên lời sửa không được gom (phải bảo "ghi lại thành luật"
  ngay); `CLAUDE.md`, settings, hook của repo kia thường không được nạp. Hợp với việc nhỏ.
- **`/dispatch <dự-án> "<việc>"`** (nên dùng): giao cho một agent chạy *trong* repo (cwd = repo, nạp
  CLAUDE.md và hook của repo), lấy repo từ field `repo:` của dashboard, chỉ mang dashboard của đúng dự án đó
  + index luật. Mặc định chỉ lập kế hoạch; `--edit` cho sửa + commit trên branch mới; push, merge, deploy,
  publish, `rm -rf` bị chặn cứng; agent bên kia không gọi được MCP của brain. Chi tiết trong
  `.claude/skills/dispatch/SKILL.md` của brain.

## 5. Key và tài khoản

Không để trong brain: brain lên git, mọi agent đọc được, và ingest xử lý nội dung.

| Loại | Để ở đâu |
|---|---|
| Key của dự án (API key, DB URL...) | `.env` của repo (gitignore) hoặc biến môi trường / secret của nền tảng deploy |
| Đăng nhập CLI (gh, vercel, neon, lark-cli...) | Mỗi máy login một lần; agent nào trên máy cũng dùng được |
| Mật khẩu, tài khoản web | Trình quản lý mật khẩu / Keychain |
| Brain chỉ ghi | Chỗ để key, không ghi giá trị: "myapp: env trên Vercel project X, local ở `.env`" |

Không dán key vào chat: chat bị gom, bước che bí mật không bắt được hết. Rào quyền trong `AGENTS.md` vẫn
áp dụng khi đã có key: push/merge prod, deploy, gửi tin cho người khác thì hỏi trước.

## 6. Nhịp huấn luyện

- Khi làm việc: AI sai thì sửa ngay và bảo "ghi lại thành luật".
- Mỗi tuần ~10 phút: `eval/lint-*.md` mới nhất (ack/sửa luật `ack: false`), `eval/review-queue.md`,
  `50-knowledge/reflection-*.md` (skill đáng tạo), `grep ok=False logs/run.log`.
- Tuần đầu chỉ cần CRITICAL.md + 10–20 luật về chính người dùng. Đừng import cả đống tài liệu.
