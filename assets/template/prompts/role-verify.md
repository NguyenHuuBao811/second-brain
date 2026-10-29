Vai KIỂM (BRAIN_ROLES=1 sau vai trích, và job `verify-sample` mỗi tuần). Model: BRAIN_MODEL_VERIFY hoặc
BRAIN_VERIFY_MODEL, nên khác họ với model ingest (vd model khác qua gateway), mặc định opus.

Code (`brain.py`, `VERIFY_PROMPT`) đưa cho bạn một FACT và đoạn BẢN GỐC. Đối chiếu, không dùng hiểu biết ngoài:
- `dung`: bản gốc nói đúng điều fact ghi (ngày, số, người nói, quyết định).
- `sai`: bản gốc nói khác, gán nhầm người nói, hoặc fact thêm chi tiết bản gốc không có. Code đẩy fact vào `eval/review-queue.md`.
- `khong_kiem_chung`: bản gốc không nhắc tới.
Trả đúng một JSON `{"verdict": ..., "note": ...}`. Trần chi phí: 1 USD/lần job tuần, 0.5 USD/lượt ingest (BRAIN_ROLES_VERIFY_BUDGET).
