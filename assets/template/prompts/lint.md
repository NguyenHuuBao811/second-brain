Lint second brain này, chỉ báo cáo, không sửa nội dung.
Nếu có `logs/check-latest.txt` (kết quả `brain.py check` tất định vừa chạy trước): chép tóm tắt vào đầu báo cáo, không kiểm lại bằng tay
những mục nó đã đo (mồ côi, link chết, thiếu related/frontmatter, stale, file > 200 dòng, INDEX lệch). Tập trung vào phần cần đọc hiểu bên dưới.
Liệt kê:
file thiếu frontmatter; wikilink gãy; file không có trong INDEX hoặc dòng INDEX trỏ file không tồn tại;
file > 200 dòng; file updated > 90 ngày; cặp file description gần giống (nghi trùng);
file `type: rule` trong `50-knowledge/rules/` thiếu `**Why:**`, `**How to apply:**` hoặc `**Bằng chứng:**`;
luật không có dòng `[[rule-...]]` trong mục `## Luật làm việc` của `50-knowledge/working-preferences.md`, hoặc dòng index trỏ luật không tồn tại;
luật có Why ghi `(suy luận, chờ xác nhận)` (liệt kê để chủ brain xác nhận);
luật `ack: false` (liệt kê kèm số dòng bằng chứng, nhiều bằng chứng lên trước, để chủ brain duyệt);
dashboard `20-projects/` thiếu `status`/`repo`/`last_activity`, thiếu một trong 5 mục cố định, hoặc `status` lệch luật (vd `active` mà `last_activity` quá 14 ngày và không nằm trong CRITICAL.md);
dashboard có `area:` trỏ file không có trong `25-areas/`, hoặc không nằm trong mục `## Dự án` của area đó; area có dự án không còn tồn tại;
dashboard dài quá 40 dòng (dấu hiệu đang chứa chi tiết, nên tách sang repo hoặc `50-knowledge/`).
Ghi kết quả vào eval/lint-<hôm nay>.md.
