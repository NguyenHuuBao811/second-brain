Dọn kiến thức cũ cho second brain này (chạy cuối tuần). Đọc AGENTS.md, INDEX.md trước. Không đọc private/, raw/, 00-inbox/.

## 1. Fact tiến độ cũ
Grep `as of` trong `20-projects/` và `30-people/team-map.md`. Một dòng là fact tiến độ khi nói về trạng thái đang diễn ra:
đang làm, blocker, chờ, tuần này, sắp xong, ai đang giữ việc gì, phase hiện tại.
Fact tiến độ có ngày "as of" cũ hơn 14 ngày so với hôm nay, và không có dòng nào mới hơn nói cùng việc đó:
- Thêm vào cuối dòng `(invalid_at: <hôm nay>, lý do: quá 14 ngày chưa xác nhận lại)`.
- Copy dòng gốc vào `archive/<tên-file>-<YYYY-MM>.md` (tạo nếu chưa có, frontmatter đúng luật).
Không đụng: quyết định, số liệu lịch sử, việc đã xong, fact có nguồn `git` mô tả việc đã làm.
Dashboard `20-projects/`: `status: active` mà `last_activity` quá 14 ngày và dự án không nằm trong CRITICAL.md thì đổi sang `idle`.

## 2. Quyết định bị đè
Trong `40-decisions/` và `20-projects/`: nếu hai fact cùng chủ thể, cùng thuộc tính mà khác nội dung, giữ fact có ngày "as of" mới hơn.
Fact cũ: thêm `invalid_at` + `superseded_by: <file hoặc dòng mới>`; file quyết định cũ đổi `Status: superseded`.
Không chắc là cùng chủ thể thì không sửa, ghi vào báo cáo mục "cần chủ brain xem".

## 2b. Luật mâu thuẫn
Đọc các file trong `50-knowledge/rules/`. Hai luật cùng tình huống mà bảo làm ngược nhau: không tự sửa, ghi cặp đó vào báo cáo mục "cần chủ brain xem".
Hai luật cùng ý (trùng): gộp bằng chứng vào file có `updated` mới hơn, file kia thêm `invalid_at` + `superseded_by`, chuyển vào `archive/`, cập nhật index trong working-preferences.md.

## 3. Review-queue
Dòng chưa tick trong `eval/review-queue.md` có ngày cũ hơn 30 ngày: xoá khỏi queue, ghi số dòng đã xoá vào báo cáo.

## 4. Kết thúc
- Ghi `eval/prune-<hôm nay>.md`: số fact invalidate theo file, số quyết định superseded, danh sách "cần chủ brain xem".
- Cập nhật `updated:` của file đã sửa, INDEX.md, append 1 dòng LOG.md.
- Không xoá fact nào khỏi vault, chỉ đánh dấu.
