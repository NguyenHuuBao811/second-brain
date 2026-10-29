# Vendor v2 — Vendor Portal

> URL: https://vendor-test.printway.work
> Nguồn: phân tích FE bundle `index-B4oII7vH.js` (2026-10-29). Rule backend chưa xác minh được đánh dấu ⚠️.
> Phía admin: xem [../vendor-v2-admin/00-README.md](../vendor-v2-admin/00-README.md).

## Danh sách màn hình

| Màn hình | Route | Điều kiện truy cập | File doc |
|---|---|---|---|
| Đăng nhập | `/login` | Chưa đăng nhập (đã login → tự chuyển về trang mặc định) | [10-dang-nhap.md](10-dang-nhap.md) |
| Đơn hàng | `/orders` | Đã đăng nhập | [11-don-hang.md](11-don-hang.md) |
| Chi tiết đơn / item | `/orders/:id`, `/orders/:id/items/:itemId` | Đã đăng nhập | [12-chi-tiet-don.md](12-chi-tiet-don.md) |
| Trạm Assize | `/production/assize` | Đã đăng nhập | [20-tram-assize.md](20-tram-assize.md) |
| Trạm Label | `/production/label` | Đã đăng nhập | [21-tram-label.md](21-tram-label.md) |
| Trạm Shipping | `/production/shipping` | Đã đăng nhập | [22-tram-shipping.md](22-tram-shipping.md) |
| Trạm sản xuất (Print/Cut/QC/Package) | `/production/step/:baseType` | Trạm sản xuất sub-barcode đang mở | [23-tram-san-xuat-sub-barcode.md](23-tram-san-xuat-sub-barcode.md) |
| Barcodes (hàng đợi sub-barcode) | `/barcodes` | Trạm sản xuất sub-barcode đang mở | [24-hang-doi-sub-barcode.md](24-hang-doi-sub-barcode.md) |
| Lỗi sản xuất | `/production-errors` | Trạm sản xuất sub-barcode đang mở | [25-loi-san-xuat.md](25-loi-san-xuat.md) |
| Sản phẩm | `/products` | Đã đăng nhập | [30-san-pham.md](30-san-pham.md) |
| Nhóm sản phẩm | `/product-groups`, `/new`, `/:id/edit` | Vendor đã bật Sub-barcode | [31-nhom-san-pham.md](31-nhom-san-pham.md) |
| Phụ kiện | `/accessories` | Vendor đã bật Sub-barcode | [32-phu-kien.md](32-phu-kien.md) |
| Partner | `/partners` | Vendor đã bật Sub-barcode | [33-partner.md](33-partner.md) |
| Menu & phân quyền | — | — | [40-menu-va-phan-quyen.md](40-menu-va-phan-quyen.md) |
| Tài khoản | `/account` | Đã đăng nhập | [41-tai-khoan.md](41-tai-khoan.md) |
| Quản lý user | `/users`, `/users/:id/permissions` | Đã đăng nhập | [42-quan-ly-user.md](42-quan-ly-user.md) |
| User của PW | `/platform-users` | super_admin, admin | [43-user-pw.md](43-user-pw.md) |
| Cài đặt vendor | `/vendor/settings` | Đã đăng nhập | [44-cai-dat-vendor.md](44-cai-dat-vendor.md) |
| Webhooks | `/webhooks` | Đã đăng nhập | [45-webhooks.md](45-webhooks.md) |
| Báo cáo | `/reports` | Permission `reports.view` | [46-bao-cao.md](46-bao-cao.md) |
| Print jobs | `/print-jobs`, `/print-jobs/:id` | Đã đăng nhập | [47-print-jobs.md](47-print-jobs.md) |
| API docs | `/api-docs` | Không chặn ở mức route | [48-api-docs.md](48-api-docs.md) |

**Quy tắc truy cập chung**
- Chưa đăng nhập → redirect **/login**. Route không tồn tại → **/login**.
- Màn "Trạm sản xuất sub-barcode đang mở": vendor không đáp ứng điều kiện → redirect **/orders**.
- Màn "Vendor đã bật Sub-barcode": vendor chưa bật → redirect **/orders**.
- Các route ghi "Đã đăng nhập" không chặn quyền ở mức route; nút/hành động bên trong ẩn hoặc hiện theo permission (xem file 40).

## Permission mặc định theo role

| Permission | owner | manager | production | shipping | viewer | staff (PW) |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| vendors.settings | ✓ | | | | | |
| users.manage | ✓ | | | | | |
| orders.read | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| orders.assize | ✓ | ✓ | ✓ | | | ✓ |
| orders.buy_label | ✓ | ✓ | ✓ | | | ✓ |
| orders.confirm_label | ✓ | ✓ | ✓ | ✓ | | ✓ |
| orders.print_label | ✓ | ✓ | ✓ | ✓ | | |
| orders.print_barcode | ✓ | ✓ | ✓ | ✓ | | |
| orders.ship | ✓ | ✓ | ✓ | ✓ | | ✓ |
| orders.reweigh | ✓ | ✓ | ✓ | | | ✓ |
| orders.back_error | ✓ | ✓ | ✓ | | | |
| orders.bulk_actions | ✓ | ✓ | ✓ | ✓ | | |
| orders.set_priority | ✓ | ✓ | ✓ | ✓ | | |
| orders.update_address | | | | | | ✓ |
| sub_barcodes.manage | ✓ | ✓ | | | | |
| production.scan | ✓ | ✓ | ✓ | | | |
| production.replace_sub_barcode | ✓ | ✓ | | | | |
| products.read | ✓ | ✓ | | ✓ | ✓ | |
| products.write | ✓ | | | | | |
| product_groups.manage | ✓ | ✓ | | | | |
| production_errors.manage | ✓ | ✓ | | | | |
| accessories.manage | ✓ | ✓ | | | | |
| partners.manage | ✓ | ✓ | | | | |
| webhooks.view | ✓ | ✓ | | | | |
| webhooks.replay | ✓ | | | | | |
| audit_logs.view | ✓ | ✓ | | | | |
| reports.view | ✓ | ✓ | | | ✓ | |
| print_boards.read | ✓ | ✓ | ✓ | | | |

⚠️ Đây là permission mặc định; owner có thể override permission theo từng user (xem [42-quan-ly-user.md](42-quan-ly-user.md)). Lưu ý vendor role mặc định **không có** `orders.update_address` — chỉ staff PW có.

## Quy tắc validate mặc định cho Input
Giống phía admin: tối đa 255 ký tự, trim, trường bắt buộc không để trống, không giới hạn ký tự đặc biệt; rule riêng ghi đè.
