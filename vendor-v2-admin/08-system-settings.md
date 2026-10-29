# System settings

Route: `/admin/system-settings` — Role: super_admin, admin. 3 tab: **FF**, **Fastway**, **Cronjob** (tab lưu trên URL `?tab=`). Thay đổi có hiệu lực trong 30s.

### Xem Inbound webhook URLs (tab FF / Fastway)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Hiển thị URL để cấu hình phía FF / Fastway gọi vào hệ thống. |
| Actor | super_admin, admin |
| Trigger | Mở tab **FF** hoặc **Fastway**. |
| Main Flow | **Tab FF** — cấu hình trên FF làm target `VENDOR_BASE_URL`:<br>Suppliers `/api/v1/external/suppliers`; Products `/api/v1/external/products`; Orders `/api/v1/external/orders`; Order canceled `…/orders/canceled`; Order refund `…/orders/refund`; Order on-hold set `…/orders/on-hold-set`; Order on-hold clear `…/orders/on-hold-clear`; Order address updated `…/orders/address-updated`; Order artwork confirmed `…/orders/error-artwork-confirmed`.<br>**Tab Fastway** — Callback `/api/v1/external/fastway/callback`, xác thực bằng header `x-fastway-key`. |
| Business Rule | Chỉ đọc. Card **Kết nối FF** (Base URL, HMAC secret) và **Sync từ FF** đang bị ẩn trên bản hiện tại. |

### Cấu hình Order auto-recovery (tab Cronjob)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Cronjob định kỳ mua lại label cho đơn lỗi label và assize lại đơn bị bỏ qua do lỗi tạm thời. |
| Actor | super_admin, admin |
| Trigger | Tab **Cronjob** → **Save settings**. |
| Main Flow | 1. Bật/tắt **Enabled** (mặc định Off).<br>2. Nhập **Interval (minutes)** (mặc định 30).<br>3. Bật/tắt **Retry failed-label orders** (mặc định On), **Retry skipped-assize orders** (mặc định On).<br>4. Click **Save settings**. |
| Post-conditions | Thành công: "Cronjob settings saved". Thất bại: "Save failed". |
| Business Rule | Hiển thị "Last run: <thời gian>" / "never". |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Interval (minutes)** * | Số nguyên ≥ 1 | — | Interval must be a whole number ≥ 1 |
