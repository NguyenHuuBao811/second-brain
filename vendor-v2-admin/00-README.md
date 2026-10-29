# Vendor v2 — Admin Portal

> URL: https://vendor-test.printway.work/admin
> Nguồn: phân tích FE bundle `index-B4oII7vH.js` (2026-10-29). Rule phía backend chưa xác minh — các mục đánh dấu ⚠️ cần dev confirm.

## Phạm vi & phân quyền

| Màn hình | Route | Role được vào | File doc |
|---|---|---|---|
| Vendors (danh sách) | `/admin` | super_admin, admin | [01-quan-ly-vendor.md](01-quan-ly-vendor.md) |
| Chi tiết Vendor | `/admin/vendors/:id` | super_admin, admin | [02-chi-tiet-vendor.md](02-chi-tiet-vendor.md) |
| All orders / Chi tiết đơn / Chi tiết item | `/admin/orders`, `/admin/orders/:id`, `/admin/orders/:id/items/:itemId` | super_admin, admin | [03-don-hang.md](03-don-hang.md) |
| Sub-barcodes | `/admin/sub-barcodes` | super_admin, admin | [04-sub-barcode.md](04-sub-barcode.md) |
| All products | `/admin/products` | super_admin, admin | [05-san-pham.md](05-san-pham.md) |
| Partners | `/admin/partners` | super_admin, admin | [06-partner.md](06-partner.md) |
| Audit log | `/admin/audit` | super_admin, admin (`requireSuperAdmin`) | [07-audit-log.md](07-audit-log.md) |
| System settings | `/admin/system-settings` | super_admin, admin (`requireSuperAdmin`) | [08-system-settings.md](08-system-settings.md) |

**Quy tắc truy cập chung**
- Chưa đăng nhập → redirect **/login**.
- Sai role / thiếu permission → hiển thị "Forbidden".
- Lưu ý: `requireSuperAdmin` trên FE thực tế cho phép cả **admin** (hàm check `role ∈ {super_admin, admin}`). ⚠️ Cần confirm có phải ý đồ nghiệp vụ không.
- Permission admin mặc định (super_admin & admin): `vendors.manage`, `system_settings.manage`, `audit_logs.view`, `admin.orders.resync`, `admin.orders.update_address`.

## Quy tắc validate mặc định cho Input
- Tối đa 255 ký tự, tự động trim khoảng trắng đầu/cuối.
- Trường bắt buộc (*) không được để trống / chỉ có khoảng trắng.
- Không giới hạn ký tự đặc biệt.
- Rule riêng của từng field (ghi trong từng doc) ghi đè rule mặc định.

## Quy ước chung của các màn danh sách
- Bộ lọc & phân trang lưu trên URL query (share link giữ nguyên filter).
- Ô tìm kiếm debounce 300ms; đổi filter → về trang 1.
- Ô tìm kiếm đa mã (Orders, Sub-barcodes): nhiều mã cách nhau bởi dấu phẩy, Tab hoặc Enter; trùng mã (không phân biệt hoa thường) tự loại.
  - Tối đa **50** mã / lần tìm; tối đa **2.000** ký tự.
- Export: **Export by filter** (bắt buộc chọn 1 vendor ở Orders/Products) và **Export selected** (các dòng đã tick).

## Thuật ngữ
| Thuật ngữ | Nghĩa |
|---|---|
| FF | Hệ thống Printway Fulfillment (nguồn supplier/product/order) |
| FW / Fastway | Đối tác vận chuyển, mua label |
| Supplier | Định danh nhà cung cấp bên FF; 1 supplier ↔ 1 vendor |
| Sub-barcode | Tem cho từng unit sản phẩm, dùng ở luồng sản xuất theo sub-barcode |
| Assize / Label / Shipping | 3 trạm: nhập kích thước–cân, mua label, xuất xưởng |
| Self-managed | Vendor dùng hệ thống riêng; nhân sự PW (role Staff) xử lý 3 trạm hộ |
