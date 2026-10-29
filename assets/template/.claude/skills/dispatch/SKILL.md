---
name: dispatch
description: Điều phối việc sang repo của một dự án từ second brain này. Giao cho một agent chạy ngay trong repo đó (nạp CLAUDE.md, settings, hook của repo), chỉ mang theo dashboard của đúng dự án đó, mặc định lập kế hoạch trước, không bao giờ push/merge/deploy. Dùng khi người dùng nói "làm việc X ở dự án Y", "giao cho repo Y", "dispatch", "điều phối sang repo", "sửa bug bên sheetsmith", hoặc muốn làm việc ở repo khác mà vẫn đứng trong brain.
---

# Dispatch: giao việc sang repo dự án

Lệnh gốc: `python3 scripts/brain.py dispatch <dự-án> "<việc>" [--edit] [--allow "<tool>"] [--model M] [--budget USD] [--dry-run]`.
`<dự-án>` là tên file trong `20-projects/` (không có `.md`). Repo lấy từ field `repo:` của dashboard.

## Các bước

1. **Xác định dự án.** `grep "^repo:" 20-projects/*.md`. Dashboard ghi `repo: none` hoặc thư mục không có trên máy này thì dừng, báo người dùng thêm đường dẫn repo vào dashboard.
2. **Viết đề bài rõ.** Một việc, có tiêu chí xong (vd "sửa lỗi X, thêm test chặn tái phát, test xanh"). Chỉ đưa những gì agent bên kia cần biết.
3. **Lập kế hoạch trước (mặc định, chỉ đọc):**
   `python3 scripts/brain.py dispatch <dự-án> "<việc>"`
   Việc dài có thể chạy tới 60 phút: chạy lệnh ở chế độ nền (`run_in_background`). Đưa kế hoạch cho người dùng xem.
4. **Chỉ khi người dùng đồng ý mới cho sửa:**
   `python3 scripts/brain.py dispatch <dự-án> "<việc + kế hoạch đã duyệt>" --edit --allow "Bash(<lệnh test của repo>:*)"`
   Lệnh test lấy từ CLAUDE.md / package.json / Makefile của repo. Agent chỉ được sửa file, chạy các lệnh git cục bộ, commit trên branch mới, và chạy đúng các lệnh `--allow`.
5. **Kiểm chứng, không tin báo cáo suông:**
   `git -C <repo> log --oneline -5`, `git -C <repo> status`, chạy lại test nếu cần.
6. **Cập nhật brain:** có commit thật thì thêm 1 dòng vào `## Trạng thái` của dashboard, kèm hash commit, as of hôm nay, nguồn `git`. Cập nhật `last_activity`, dòng INDEX, và append LOG.md. Việc agent ghi ở "Cần chủ brain duyệt" thì chuyển vào `## Đang treo`.
7. **Báo người dùng:** đã làm gì, branch và commit, test, việc chờ duyệt. Push, merge, deploy là quyết định của người dùng: hỏi, không tự làm.

## Luật

- **Không bao giờ cho phép** push, `gh pr merge`, deploy prod, publish, `rm -rf`, `git reset --hard`. Lệnh đã chặn sẵn; không tìm cách vòng qua (vd chạy qua script khác).
- **Không truyền key/secret.** Agent trong repo dùng `.env` của repo hoặc CLI đã đăng nhập sẵn trên máy (gh, vercel, neon...). Brain chỉ ghi *chỗ để* key, không ghi giá trị. Người dùng dán key vào chat thì nhắc họ đổi key và để vào `.env`.
- **Chỉ dashboard của đúng dự án đó đi theo.** Không thêm thông tin dự án khác, người khác, công ty khác vào đề bài. Repo có người ngoài (lab, khách): hỏi người dùng trước khi đưa nghiệp vụ nội bộ vào đề bài.
- Agent trong repo không gọi được MCP của brain (đã chặn), nên không đọc ngược được brain.
- Phiên dispatch không bị `collect` gom (đánh dấu phiên tự động). Bài học rút ra từ kết quả thì ghi thành luật trong session này.
- Log mỗi lần chạy: `logs/dispatch/<thời-điểm>-<dự-án>.md` (không vào git).
