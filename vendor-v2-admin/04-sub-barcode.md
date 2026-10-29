# Sub-barcodes (cross-vendor)

Route: `/admin/sub-barcodes` — Role: super_admin, admin. Subtitle: "Sub-barcode của mọi vendor."

### Xem danh sách Sub-barcode

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Tra cứu sub-barcode (unit) của mọi vendor. Màn chỉ đọc + export. |
| Actor | super_admin, admin |
| Trigger | Menu **Sub-barcodes**. |
| Main Flow | 1. Hiển thị bảng: **Vendor**, **Sub-barcode**, **Đơn hàng / Mã vạch đơn** (link sang chi tiết đơn), **Tracking**, **Loại đơn**, **Sản phẩm**, **Trạng thái**, **Ngày**, **Note sản xuất**, **Ghi chú QC**, **Ngày nhận**, **Thiết kế** (link Xem).<br>2. Mặc định 20 dòng/trang (20/50/100). |
| Alternative Flow | Không có dữ liệu → "Không có dữ liệu". |
| Business Rule | **Bộ lọc:** tìm kiếm (sub-barcode, mã đơn, tracking — đa mã), Khoảng ngày, Vendor, Loại sản phẩm, chip Trạng thái (chọn nhiều).<br>- Trạng thái unit (ưu tiên từ trên xuống): Canceled → Broken → Artwork Error → QC-error → theo trạng thái đơn (Assize / Label / Shipping) → bước workflow cuối đã qua (Printed / Cut / QC-passed / Packaged) → Exported-barcode → Pre-production → New.<br>- Đơn On Hold: dùng trạng thái trước khi hold.<br>- Danh sách **Loại sản phẩm** lấy từ dữ liệu trang hiện tại.<br>- Đổi filter → bỏ chọn các dòng đã tick. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Search** | ≤ 50 mã | Tối đa 50 mã một lần tìm | — |
| **Search** | ≤ 2.000 ký tự | Nội dung tìm kiếm quá dài (tối đa 2000 ký tự) | — |
| **Search** | ≥ 1 mã | Nhập ít nhất một mã | — |

### Export Sub-barcode

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xuất danh sách sub-barcode. |
| Actor | super_admin, admin |
| Trigger | Nút **Export**. |
| Main Flow | **Export theo bộ lọc (N)** hoặc **Export đã chọn (N)**. |
| Exception Flow | "Export thất bại, vui lòng thử lại". |
| Business Rule | - Export theo bộ lọc disable khi ô search không hợp lệ (không bắt buộc chọn vendor).<br>- Export đã chọn cần ≥ 1 dòng tick. |
