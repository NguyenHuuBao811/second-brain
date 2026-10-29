# Webhooks

Route: `/webhooks` — Role-permission: xem `webhooks.view` (owner, manager); replay `webhooks.replay` (owner). ⚠️ Không có mục menu nào trỏ tới màn này (chỉ vào bằng URL) và route không có guard permission trên FE — chặn xem dựa vào backend.

Text màn này chỉ có tiếng Anh.

### Xem log webhook

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem nhật ký gửi webhook ra ngoài (outbound) của vendor. |
| Actor | owner, manager |
| Trigger | Mở `/webhooks`. |
| Main Flow | 1. Tiêu đề **Webhook events** — "Outbound delivery log".<br>2. Thanh lọc: dropdown trạng thái (**All statuses** / **Pending** / **Sent** / **Failed** / **Skipped**), công tắc **Failed only**, tổng "<n> events".<br>3. Bảng: **Status** (badge), **Event**, **Attempts**, **Created**, **Last error** ("—" nếu không có).<br>4. Click 1 dòng → panel chi tiết bên phải: tên event, badge status, **ID**, **Attempts**, **Created**, **Completed**, **Next retry** (nếu có), **Last error** (nếu có), **Payload** (JSON). |
| Alternative Flow | A1. **Refresh** → tải lại danh sách (toast "Refreshing…").<br>A2. Không có dữ liệu → "No webhook events yet" — "Events will appear here when webhooks are dispatched." |
| Business Rule | - Chỉ hiển thị tối đa **100** event mới nhất, không phân trang. ⚠️ Thứ tự sắp xếp do backend quyết định.<br>- Bật **Failed only** = lọc status Failed và xoá lựa chọn dropdown; chọn dropdown thì tắt Failed only.<br>- Bộ lọc lưu trên URL. |

### Replay webhook

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Gửi lại một webhook event đã thất bại. |
| Actor | owner (user có `webhooks.replay`) |
| Trigger | Trong panel chi tiết event có status **failed** → click **Replay event**. |
| Pre-conditions | Event có status failed; user có `webhooks.replay`. |
| Post-conditions | Thành công: toast "Replay enqueued", đóng panel, danh sách tải lại. Thất bại: "Replay failed". |
| Main Flow | 1. Mở event failed.<br>2. Click **Replay event** (đang xử lý → "Replaying…").<br>3. Hệ thống đưa event vào hàng đợi gửi lại. |
| Business Rule | - Nút chỉ hiện khi status = failed và user có quyền replay.<br>- Không có popup xác nhận.<br>- Replay là bất đồng bộ (enqueue) — kết quả xem lại bằng **Refresh**. |
