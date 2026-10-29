# Trạm Shipping

Route: `/production/shipping` — Menu **Scanning › Shipping**: role staff thấy theo role; role vendor thấy khi có permission `orders.ship` (owner, manager, production, shipping). Route không chặn quyền; nút trong trang không check permission ở FE ⚠️.

Bố cục: tiêu đề **Shipping**, ô quét tracking, cột trái = artwork + card thông tin ship, cột phải = panel đơn & unit.

### Quét tracking number

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Quét tracking number của kiện để xác định đơn cần ship. |
| Actor | staff, owner, manager, production, shipping |
| Trigger | Quét/gõ mã + Enter hoặc **Enter barcode**. |
| Pre-conditions | Đơn đã có tracking number; trạng thái Labeled hoặc Shipped. |
| Post-conditions | Hiển thị card **Tracking**, **Carrier**, **Dims** (D×R×C cm, cân nặng g). |
| Main Flow | 1. Placeholder "Quét tracking number…", hint "Bắt buộc quét tracking number của đơn".<br>2. Hệ thống tra cứu đơn theo mã.<br>3. Mã quét phải khớp tracking number của đơn → hiển thị card + nút **Confirm ship ↵**. |
| Alternative Flow | A1. Đơn đã **Shipped** → toast "Đơn đã Shipped — xem lại thông tin", card hiển thị "Đơn đã Shipped — không thể submit lại" (không có nút ship). |
| Exception Flow | E1. Mã không phải tracking của đơn (vd quét mã đơn/sub-barcode) → "Phải quét đúng tracking number của đơn".<br>E2. Trạng thái khác Labeled/Shipped → "Order chưa ở bước Ship (current: {status})".<br>E3. Labeled nhưng đang chờ label mới → cảnh báo "Order đang chờ label mới (pendingRelabel)".<br>E4. 404 → "Order không tìm thấy"; khác → "Lỗi tra cứu". |
| Business Rule | So khớp tracking: chấp nhận mã quét đúng bằng tracking, hoặc mã barcode carrier dài được cắt về tracking theo độ dài (30 ký tự → bỏ 8 ký tự đầu; 34 → bỏ 12 đầu; 28 → bỏ 7 đầu và 5 cuối; 41 → bỏ 18 đầu). |

### Xác nhận ship

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Đánh dấu đơn đã giao cho hãng vận chuyển. |
| Actor | staff, owner, manager, production, shipping (permission `orders.ship` ⚠️ BE) |
| Trigger | Click **Confirm ship ↵**. |
| Pre-conditions | Đơn Labeled, không chờ relabel, đã quét đúng tracking. |
| Post-conditions | Đơn → **Shipped**; toast "Order {pwOrderId} → Shipped"; reset, focus lại ô quét. |
| Main Flow | 1. Click **Confirm ship ↵** ("Shipping…").<br>2. Hệ thống cập nhật trạng thái. |
| Exception Flow | Lỗi → "Ship failed". |
