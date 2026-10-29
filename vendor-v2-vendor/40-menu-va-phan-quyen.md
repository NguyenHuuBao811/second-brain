# Menu & Phân quyền (phía Vendor)

Route: toàn app (layout chung: sidebar + header) — Role: mọi user đã đăng nhập.

**Quy tắc truy cập chung**
- Chưa đăng nhập → redirect **/login**. Đăng nhập xong: super_admin/admin → `/admin`; các role khác → `/orders`.
- Route có guard: sai role / thiếu permission → trang chỉ hiện "Forbidden".
- Route cấu hình sub-barcode (Nhóm sản phẩm, Phụ kiện, Partner) cần vendor bật **Sub-barcode**; route sản xuất (trạm quét theo bước, Barcodes, Lỗi sản xuất) cần **luồng sản xuất sub-barcode đang mở**. Không thỏa → redirect `/orders`.
- ⚠️ Nhiều route vendor **không có guard permission trên FE** (chỉ cần đăng nhập): `/users`, `/users/:id/permissions`, `/vendor/settings`, `/webhooks`, `/print-jobs`, `/print-jobs/:id`, `/account`. Việc chặn phụ thuộc backend → cần dev confirm.
- Check permission trên FE: user có permission trong danh sách `permissions` (đã gồm role default + override). Riêng super_admin/admin được coi như có thêm toàn bộ permission của role **staff**.

### Ma trận Role × Permission mặc định

Role vendor: **owner, manager, production, shipping, viewer**. Role platform (PW): **super_admin, admin, staff** (admin có cùng bộ quyền với super_admin).

| Permission | Ý nghĩa (VI) | owner | manager | production | shipping | viewer | staff | super_admin / admin |
|---|---|---|---|---|---|---|---|---|
| `vendors.manage` | Quản lý vendor |  |  |  |  |  |  | ✓ |
| `vendors.settings` | Cài đặt vendor | ✓ |  |  |  |  |  |  |
| `users.manage` | Quản lý người dùng | ✓ |  |  |  |  |  |  |
| `system_settings.manage` | Quản lý cài đặt hệ thống |  |  |  |  |  |  | ✓ |
| `orders.read` | Xem đơn hàng | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |  |
| `orders.assize` | Đo đơn hàng (assize) | ✓ | ✓ | ✓ |  |  | ✓ |  |
| `orders.buy_label` | Mua label vận chuyển | ✓ | ✓ | ✓ |  |  | ✓ |  |
| `orders.confirm_label` | Xác nhận label | ✓ | ✓ | ✓ | ✓ |  | ✓ |  |
| `orders.print_label` | In label | ✓ | ✓ | ✓ | ✓ |  |  |  |
| `orders.print_barcode` | In barcode | ✓ | ✓ | ✓ | ✓ |  |  |  |
| `sub_barcodes.manage` | Manage the barcode queue | ✓ | ✓ |  |  |  |  |  |
| `production.scan` | Scan production step | ✓ | ✓ | ✓ |  |  |  |  |
| `production.replace_sub_barcode` | Replace a QC-failed sub-barcode | ✓ | ✓ |  |  |  |  |  |
| `orders.ship` | Ship đơn hàng | ✓ | ✓ | ✓ | ✓ |  | ✓ |  |
| `orders.back_error` | Báo lỗi artwork | ✓ | ✓ | ✓ |  |  |  |  |
| `orders.reweigh` | Cân lại đơn | ✓ | ✓ | ✓ |  |  | ✓ |  |
| `orders.bulk_actions` | Thao tác hàng loạt | ✓ | ✓ | ✓ | ✓ |  |  |  |
| `orders.set_priority` | Set order priority | ✓ | ✓ | ✓ | ✓ |  |  |  |
| `orders.update_address` | Edit shipping address |  |  |  |  |  | ✓ |  |
| `admin.orders.resync` | Resync order to FF |  |  |  |  |  |  | ✓ |
| `admin.orders.update_address` | Edit shipping address (admin) |  |  |  |  |  |  | ✓ |
| `products.read` | Xem sản phẩm | ✓ | ✓ |  | ✓ | ✓ |  |  |
| `products.write` | Sửa sản phẩm | ✓ |  |  |  |  |  |  |
| `product_groups.manage` | Manage product groups | ✓ | ✓ |  |  |  |  |  |
| `production_errors.manage` | Manage production errors | ✓ | ✓ |  |  |  |  |  |
| `accessories.manage` | Manage accessories | ✓ | ✓ |  |  |  |  |  |
| `partners.manage` | Manage partners | ✓ | ✓ |  |  |  |  |  |
| `webhooks.view` | Xem webhooks | ✓ | ✓ |  |  |  |  |  |
| `webhooks.replay` | Replay webhook | ✓ |  |  |  |  |  |  |
| `audit_logs.view` | Xem audit log | ✓ | ✓ |  |  |  |  | ✓ |
| `reports.view` | Xem báo cáo | ✓ | ✓ |  |  | ✓ |  |  |
| `print_boards.read` | View print boards | ✓ | ✓ | ✓ |  |  |  |  |

Ghi chú: Tên permission chưa có bản dịch VI trong app (hiển thị EN) được giữ nguyên tiếng Anh ở cột Ý nghĩa.

### Hiển thị Sidebar theo điều kiện

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Sidebar trái liệt kê menu theo nhóm; chỉ hiện mục user được phép. Nhóm không còn mục nào thì ẩn cả nhóm. |
| Actor | Mọi user đã đăng nhập |
| Trigger | Mở bất kỳ trang nào trong app. |
| Pre-conditions | Đã đăng nhập. |
| Main Flow | 1. Đầu sidebar: logo + **Vendor Mini App** + mã vendor (super_admin/admin không có vendor → "Super admin").<br>2. Hệ thống dựng danh sách menu theo role, permission và cờ của vendor (bảng dưới).<br>3. Mục có điều kiện role → chỉ hiện khi role khớp; mục có điều kiện permission → chỉ hiện khi user có permission đó.<br>4. Mục đang mở được highlight. Footer: "v2.0 · operational". |
| Business Rule | - Sidebar chỉ hiện ở màn hình ≥ md; màn hình nhỏ không có sidebar. ⚠️ Chưa thấy menu thay thế cho mobile.<br>- Cờ vendor dùng cho menu: **subBarcodeEnabled** (bật luồng sub-barcode), **subBarcodeProductionOpen** (luồng sản xuất sub-barcode đang mở), **apiAccessEnabled**.<br>- ⚠️ Cờ **selfManaged** có trong user nhưng không được dùng để lọc menu. |

#### Bảng menu

| Nhóm (VI) | Mục | Route | Điều kiện hiển thị |
|---|---|---|---|
| Đơn hàng | **Orders** | `/orders` | Role ≠ admin; permission `orders.read` |
| Catalog | **Products** | `/products` | Role vendor (không phải admin/staff); `products.read` |
| Catalog | **Quản lý Nhóm sản phẩm** | `/product-groups` | subBarcodeEnabled; `products.read` |
| Catalog | **Sub-barcode** | `/barcodes` | subBarcodeProductionOpen; `orders.read` |
| Catalog | **Lỗi sản xuất** | `/production-errors` | subBarcodeProductionOpen; `production_errors.manage` |
| Catalog | **Bàn in** | `/print-jobs` | `print_boards.read` |
| Catalog | **Phụ kiện** | `/accessories` | subBarcodeEnabled; `accessories.manage` |
| Catalog | **Partner** | `/partners` | subBarcodeEnabled; `partners.manage` |
| Quét sản xuất | Các bước sản xuất của vendor (vd. **Print**, **Cut**, **QC**, **Package**) | `/production/step/:baseType` | Role vendor; subBarcodeProductionOpen; `production.scan`. Danh sách bước lấy từ cấu hình workflow của vendor. |
| Quét sản xuất | **Assize** | `/production/assize` | Role staff → luôn hiện; role khác → `orders.assize` |
| Quét sản xuất | **Label** | `/production/label` | Role staff → luôn hiện; role khác → `orders.print_label` |
| Quét sản xuất | **Shipping** | `/production/shipping` | Role staff → luôn hiện; role khác → `orders.ship` |
| Phân tích | **Reports** | `/reports` | Role vendor; `reports.view` |
| Quản lý | **Users** | `/users` | Role vendor; `users.manage` |
| Quản lý | **Vendor settings** | `/vendor/settings` | Role vendor; `vendors.settings` |
| Quản lý | **API docs** | `/api-docs` | Vendor bật apiAccessEnabled **và** role = owner |
| Quản trị | **Vendors**, **User PW**, **All orders**, **Sub-barcode**, **Bàn in**, **All products**, **Partner**, **Audit log**, **Cài đặt hệ thống** | `/admin`, `/platform-users`, `/admin/orders`, `/admin/sub-barcodes`, `/print-jobs`, `/admin/products`, `/admin/partners`, `/admin/audit`, `/admin/system-settings` | Role super_admin, admin |
| Luồng riêng | **Orders**, **Assize**, **Label**, **Shipping** | `/orders`, `/production/assize`, `/production/label`, `/production/shipping` | Role super_admin, admin |

Tổng hợp theo role (mặc định, chưa override):
- **owner**: Orders, Products, Bàn in, Assize/Label/Shipping, Reports, Users, Vendor settings, API docs (nếu bật API) + các mục sub-barcode theo cờ.
- **manager**: như owner trừ Users, Vendor settings, API docs.
- **production**: Orders, Bàn in, Assize/Label/Shipping, bước quét sản xuất (nếu luồng mở).
- **shipping**: Orders, Products, Label, Shipping.
- **viewer**: Orders, Products, Reports.
- **staff**: Orders, Assize, Label, Shipping.
- **super_admin / admin**: nhóm Quản trị + Luồng riêng.
- ⚠️ Màn **Webhooks** (`/webhooks`) không có mục menu nào — chỉ vào được bằng URL trực tiếp.

### Header

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Thanh trên cùng: breadcrumb, đổi ngôn ngữ, đổi theme, menu tài khoản. |
| Actor | Mọi user đã đăng nhập |
| Trigger | Thao tác trên header. |
| Main Flow | 1. Breadcrumb **<Nhóm> / <Mục>** theo mục menu khớp route hiện tại (khớp dài nhất).<br>2. Icon địa cầu: đổi VI ↔ EN (tooltip "Switch to EN" / "Chuyển sang VI").<br>3. Icon theme → menu **Theme**: **light / dark / system** (dấu tick ở mục đang chọn).<br>4. Nút user (username + role) → dropdown: username, "<mã vendor hoặc Super admin> · <role>", **Account** (→ `/account`), **Đăng xuất**. |
| Post-conditions | Đăng xuất → về **/login**. |
| Business Rule | - Đổi ngôn ngữ ở header được **lưu vào tài khoản** (server) và áp dụng ngay.<br>- Đổi theme ở header chỉ lưu trên trình duyệt (localStorage), **không** lưu vào tài khoản; muốn lưu dùng màn **Account**. |
