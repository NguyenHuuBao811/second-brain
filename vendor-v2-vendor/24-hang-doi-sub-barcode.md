# Barcodes (hàng đợi sub-barcode)

Route: `/barcodes` (`?tab=standard|fba|priority|all|qcErrors|exports`) — Chỉ vào được khi vendor có trạm sản xuất sub-barcode đang mở, ngược lại redirect **/orders**. Menu **Catalog › Sub-barcode**: permission `orders.read`.
Permission trong trang:
- `sub_barcodes.manage` (owner, manager): thấy tab **Sub-barcode (Standard)**, **FBA**, **Priority**, **QC error**, **Lịch sử export**. Không có quyền → chỉ thấy tab **All Sub-barcode** (tab mặc định khi đó).
- `orders.print_barcode` (owner, manager, production, shipping): nút **Export sub-barcode**, **Get sub-barcode**, **Tải lại** (lịch sử export).
- `production.replace_sub_barcode` (owner, manager): nút **Gen new barcode** ở tab QC error.

Tiêu đề **Sub-barcode**. Tab mặc định (có quyền): **Sub-barcode**; `tab=pending` cũ → Standard.

### Xem hàng đợi theo sản phẩm (tab Sub-barcode / FBA / Priority)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem các nhóm sản phẩm có unit đang chờ in tem theo từng hàng đợi. |
| Actor | owner, manager (`sub_barcodes.manage`) |
| Trigger | Chọn tab **Sub-barcode ({count})**, **FBA ({count})** hoặc **Priority ({count})**. |
| Main Flow | 1. Bảng cột **Sản phẩm**, **Loại sản phẩm**, **Số lượng** (số unit), **Trạng thái** (luôn **Pre-production**).<br>2. Chọn checkbox các dòng để export. |
| Business Rule | - Số trên tab = số nhóm sản phẩm (dòng) trong hàng đợi.<br>- Tên sản phẩm trống → "Chưa xác định". Bảng trống → "Không có dữ liệu".<br>- Đổi tab → xoá lựa chọn. |

### Get sub-barcode

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Kéo các unit mới vào hàng đợi đang xem để chuẩn bị in tem. |
| Actor | owner, manager (cần cả tab hàng đợi `sub_barcodes.manage` và `orders.print_barcode`) |
| Trigger | Click **Get sub-barcode ({count})** ở tab Standard/FBA/Priority. |
| Pre-conditions | Số unit có thể lấy > 0 (nút disable khi 0 hoặc đang chạy). |
| Post-conditions | Toast "Đã lấy {units} sub-barcode của {orders} đơn"; refresh hàng đợi & đơn hàng. |
| Main Flow | 1. Nút hiển thị số unit có thể lấy cho hàng đợi hiện tại.<br>2. Click → hệ thống lấy sub-barcode. |
| Exception Flow | E1. Không có gì để lấy → info "Không có sub-barcode nào cần lấy".<br>E2. Lỗi → "Lấy sub-barcode thất bại". |
| Business Rule | ⚠️ Tiêu chí unit nào được đưa vào Standard/FBA/Priority do BE quyết định. |

### Export sub-barcode (file tem)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xuất file tem (zip) cho các nhóm sản phẩm đã chọn trong hàng đợi. |
| Actor | owner, manager (`sub_barcodes.manage` + `orders.print_barcode`) |
| Trigger | Chọn dòng → click **Export sub-barcode ({count})**. |
| Pre-conditions | Có ≥ 1 dòng được chọn. |
| Post-conditions | Tải `BarcodeExport.zip`; lựa chọn reset; refresh hàng đợi. Unit chuyển **Exported-barcode** ⚠️ (BE); lần export ghi vào **Lịch sử export**. |
| Main Flow | 1. Tick các nhóm sản phẩm.<br>2. Click **Export sub-barcode ({count})** (disable khi đang chạy). |
| Exception Flow | E1. `no_units` → info "Không còn sub-barcode nào để export".<br>E2. 403 → "Bạn không có quyền export sub-barcode".<br>E3. Khác → "Export thất bại, vui lòng thử lại". |
| Business Rule | Phải export trước khi quét sản xuất (xem [23](23-tram-san-xuat-sub-barcode.md)). |

### Tra cứu tất cả sub-barcode (tab All Sub-barcode)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Tìm kiếm, lọc và xuất Excel danh sách sub-barcode của vendor. |
| Actor | Mọi user có `orders.read` (owner, manager, production, shipping, viewer) |
| Trigger | Chọn tab **All Sub-barcode ({count})**. |
| Main Flow | 1. Ô tìm: "Tìm theo sub-barcode, mã đơn, tracking... (nhiều mã cách nhau bởi dấu phẩy, Tab hoặc Enter)" (debounce 300ms).<br>2. Bộ lọc: **Khoảng ngày**, **Tất cả loại sản phẩm** (lấy từ dữ liệu trang hiện tại), chip trạng thái chọn nhiều: Canceled, Broken, Artwork Error, QC-error, New, Pre-production, Exported-barcode, Printed, Cut, QC-passed, Packaged, Assize, Label, Shipping.<br>3. Bảng: **Sub-barcode**, **Đơn hàng / Mã vạch đơn** (link sang chi tiết đơn + copy), **Tracking**, **Loại đơn**, **Sản phẩm** (tên + SKU), **Trạng thái** (kèm công đoạn cuối), **Ngày**, **Note sản xuất**, **Ghi chú QC**, **Ngày nhận**, **Thiết kế** (link **Xem**).<br>4. Phân trang server 20/50/100.<br>5. Menu **Export**: **Export theo bộ lọc ({count})** hoặc **Export đã chọn ({count})** → tải file .xlsx. |
| Exception Flow | E1. Tìm > 50 mã → "Tối đa {max} mã một lần tìm"; > 2000 ký tự → "Nội dung tìm kiếm quá dài (tối đa {max} ký tự)"; không có mã nào → "Nhập ít nhất một mã". Khi lỗi, không gọi danh sách và **Export theo bộ lọc** disable.<br>E2. Export lỗi → "Export thất bại, vui lòng thử lại". |
| Business Rule | Bộ lọc lưu trên URL (q, from, to, productType, status…). Lọc ngày từ 00:00:00 đến 23:59:59.999 (UTC). Export đã chọn disable khi chưa chọn dòng. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Ô tìm kiếm** | Tối đa 50 mã | Tối đa {{max}} mã một lần tìm | At most {{max}} codes per search |
| **Ô tìm kiếm** | Tối đa 2000 ký tự | Nội dung tìm kiếm quá dài (tối đa {{max}} ký tự) | Search text is too long (max {{max}} characters) |
| **Ô tìm kiếm** | Có nội dung thì phải có ≥ 1 mã | Nhập ít nhất một mã | Enter at least one code |

### Xem lỗi QC (tab QC error)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Danh sách unit bị báo lỗi QC. |
| Actor | owner, manager (`sub_barcodes.manage`) |
| Trigger | Chọn tab **QC error ({count})** (count = số lỗi Chờ xử lý). |
| Main Flow | 1. Chip lọc trạng thái (chọn 1): **Chờ xử lý**, **Đã xử lý**, **Đã thay tem**.<br>2. Bảng: checkbox, **Mã đơn** (link), **Sub-barcode**, **Sản phẩm**, **Ngày**, **Công đoạn** (bị đổ lỗi), **Tên lỗi**, **Ảnh QC** (tối đa 3 thumbnail, click phóng to), **Trạng thái**.<br>3. Phân trang 20/50/100. |
| Business Rule | Chỉ dòng **Chờ xử lý** chọn được; checkbox header "Chọn tất cả lỗi chờ xử lý trong trang". ⚠️ Khi nào lỗi chuyển **Đã xử lý** do BE quyết định. |

### Gen new barcode (thay tem lỗi QC)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Huỷ unit lỗi QC và tạo sub-barcode mới thay thế, tải file tem mới. |
| Actor | owner, manager (`production.replace_sub_barcode`) |
| Trigger | Tab QC error → chọn dòng → **Gen new barcode ({count})**. |
| Pre-conditions | ≥ 1 lỗi Chờ xử lý được chọn. |
| Post-conditions | Tải `BarcodeExport.zip` chứa tem mới; toast "Đã tạo {count} tem mới"; tem cũ thành **Broken** (quét tem cũ sẽ báo dùng tem mới); lỗi → **Đã thay tem**. |
| Main Flow | 1. Chọn lỗi.<br>2. Click **Gen new barcode ({count})** (disable khi đang chạy). |
| Exception Flow | E1. 403 → "Bạn không có quyền tạo tem thay thế".<br>E2. `sub_barcode_already_broken` → "Sub-barcode đã được thay tem từ trước".<br>E3. `sub_barcode_inactive` → "Sub-barcode đã bị hủy, không thể tạo tem thay thế".<br>E4. `sub_barcode_no_open_qc_error` → "Sub-barcode này không có lỗi QC đang chờ xử lý".<br>E5. Khác → "Tạo tem mới thất bại". |
| Business Rule | Hành động xoá sổ hàng đã sản xuất, tách quyền riêng với quét sản xuất. Không có confirm ở FE. |

### Lịch sử export / Tải lại file

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem các lần export tem và tải lại file. |
| Actor | Xem: owner, manager (`sub_barcodes.manage`). Tải lại: thêm `orders.print_barcode`. |
| Trigger | Chọn tab **Lịch sử export**. |
| Main Flow | 1. Ghi chú: "File tải lại lấy dữ liệu hiện tại của đơn hàng, nên có thể khác với file gốc nếu đơn hàng đã được chỉnh sửa sau khi export."<br>2. Bảng: **Tên file**, **Tab** (Sub-barcode/FBA/Priority), **Số unit**, **Sản phẩm đã chọn** (số nhóm), **Thời gian export**, **Người export**, nút **Tải lại**.<br>3. Click **Tải lại** → tải file với tên gốc. |
| Exception Flow | E1. 403 → "Bạn không có quyền tải lại file export".<br>E2. `export_batch_units_deleted` → "Không thể tạo lại file export này: các sub-barcode trong file đã bị xoá".<br>E3. Khác → "Tải lại file export thất bại, vui lòng thử lại". |
| Business Rule | Trống → "Chưa có lần export nào". Phân trang 20/50/100. |
