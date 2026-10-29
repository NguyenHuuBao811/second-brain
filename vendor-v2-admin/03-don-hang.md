# Đơn hàng (All orders)

Routes: `/admin/orders`, `/admin/orders/:id`, `/admin/orders/:id/items/:itemId` — Role: super_admin, admin.

### Xem danh sách đơn (cross-vendor)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem đơn của mọi vendor, lọc và export. |
| Actor | super_admin, admin |
| Trigger | Menu **All orders**. |
| Main Flow | 1. Mặc định lọc **30 ngày gần nhất** theo ngày tạo, 100 dòng/trang.<br>2. Hiển thị bảng: **Vendor**, **PW Order ID**, **Type**, **Production flow**, **Products**, **Artwork**, **Ship fee**, **Tracking**, **Status**, **Received**, **Qty**.<br>3. Click dòng → Chi tiết đơn. |
| Alternative Flow | A1. Đơn ≥ 2 item → mở rộng dòng xem từng item.<br>A2. **Artwork** → popup xem thiết kế.<br>A3. Badge **Lỗi label** ở Tracking → popup "Lỗi mua label Fastway" hiển thị lý do.<br>A4. **Refresh** → tải lại.<br>A5. Không có kết quả → "No orders match your filters" + reset filter. |
| Business Rule | **Bộ lọc:** tìm kiếm (mã đơn / tên đơn, đa mã), Vendor, Status, Type, Tình trạng label, Khoảng ngày.<br>- Status: New, In production, Assized, Labeled, Shipped, Artwork Error, On Hold, Canceled, Shipping Refunded.<br>- Type: Basic, TikTok, TikTok by seller, Sample, Bulk.<br>- Tình trạng label: Đã có label / Chưa có label / Label lỗi.<br>- Page size: 20 / 50 / 100 / 200.<br>- Đơn có toàn bộ item bị cancel → dòng gạch ngang.<br>- 1 item: hiện tên SP · variant + SKU; nhiều item: "N items · X canceled" + loại SP. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Search** | ≤ 50 mã | Tối đa 50 mã một lần tìm. | — |
| **Search** | ≤ 2.000 ký tự | Chuỗi tìm kiếm quá dài, tối đa 2000 ký tự. | — |
| **Search** | Có ít nhất 1 mã hợp lệ | Không có mã đơn nào để tìm. | — |

### Export đơn hàng

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xuất file đơn theo bộ lọc hoặc theo dòng đã chọn. |
| Actor | super_admin, admin |
| Trigger | Nút **Export**. |
| Main Flow | **Export by filter (N)**: xuất toàn bộ đơn khớp filter hiện tại.<br>**Export selected (N)**: xuất các dòng đã tick. |
| Exception Flow | Lỗi → "Export thất bại". |
| Business Rule | - Export by filter chỉ bật khi đã chọn **1 vendor** và ô search hợp lệ.<br>- Export selected chỉ bật khi đã tick ≥ 1 dòng. |

### Xem chi tiết đơn

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem đầy đủ thông tin 1 đơn (chế độ admin). |
| Actor | super_admin, admin |
| Trigger | Click 1 đơn trong danh sách. |
| Main Flow | 1. Header: PW Order ID (copy), Partner code, ngày tạo, Status, Type, số vendor, Production flow, badge **Re-weighing** (nếu đang cân lại), Vendor.<br>2. Thanh tiến độ: unit đã xong / tổng, các mốc Assize → Label → Shipped.<br>3. Cột trái: danh sách **Items**.<br>4. Cột phải: Hoạt động/Labels (audit log, tải thêm), Thông tin vận chuyển (tracking, phí ship), Địa chỉ giao hàng, Kích thước, Routing events. |
| Alternative Flow | A1. Đơn TikTok có label từ FF → link "Xem label TikTok".<br>A2. Đơn **On Hold** → banner "Đơn đang On Hold bởi FF" + thời điểm + lý do.<br>A3. Click item → Chi tiết item. |

### Sửa địa chỉ giao hàng (admin)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Admin sửa địa chỉ người nhận của đơn bất kỳ vendor. |
| Actor | super_admin, admin (permission `admin.orders.update_address`) |
| Trigger | Nút **Sửa** ở card địa chỉ. |
| Pre-conditions | Status ∉ {Shipped, Canceled, Shipping Refunded, On Hold}. |
| Post-conditions | Thành công: "Đã cập nhật địa chỉ", lý do ghi vào lịch sử hoạt động. Thất bại: hiện lỗi API. |
| Main Flow | 1. Mở popup **Sửa địa chỉ giao hàng**.<br>2. Sửa các field.<br>3. Click **Lưu** → popup **Xác nhận sửa địa chỉ**, nhập **Lý do chỉnh sửa**.<br>4. Click **Xác nhận & lưu**. |
| Alternative Flow | Đơn **Labeled** → cảnh báo "Đơn đã mua label — sửa địa chỉ sẽ KHÔNG cập nhật lên label đã in." |
| Business Rule | - **Quốc gia** khoá: "Không thể đổi quốc gia (ảnh hưởng dịch vụ vận chuyển)."<br>- Đổi Tỉnh/Bang → xoá Thành phố. Tỉnh/Thành phố là combobox gợi ý; không có gợi ý vẫn lưu text đã nhập.<br>- Field trống không gửi lên. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Tên người nhận** | Optional | — | — |
| **Số điện thoại** | Optional | — | — |
| **Email** | Optional | — | — |
| **Mã số thuế** | Optional | — | — |
| **Địa chỉ 1** * | Bắt buộc | (Nút **Lưu** disable) | — |
| **Địa chỉ 2** | Optional | — | — |
| **Quốc gia** | Read-only | — | — |
| **Tỉnh/Bang** | Chỉ nhập khi có quốc gia | — | — |
| **Thành phố** | Chỉ nhập khi có tỉnh | — | — |
| **Mã bưu chính** | Optional | — | — |
| **Lý do chỉnh sửa** | ⚠️ Cần confirm bắt buộc hay không | — | — |

### Xem chi tiết item (sub-barcode units)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem các unit (sub-barcode) của 1 item trong đơn. |
| Actor | super_admin, admin |
| Trigger | Click item trong Chi tiết đơn. |
| Main Flow | 1. Sidebar trái: danh sách item của đơn.<br>2. Header: tên SP, SKU, loại SP, barcode, trạng thái sản xuất.<br>3. Danh sách **Đơn vị sản phẩm (N)**, 10 unit/trang, nút Trước/Sau.<br>4. **Xem artwork** → popup thiết kế (tải được file). |
| Alternative Flow | Item không dùng sub-barcode → "Sản phẩm này không dùng sub-barcode". |
