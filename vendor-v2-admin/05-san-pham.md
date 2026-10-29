# Sản phẩm (All products)

Route: `/admin/products` — Role: super_admin, admin.

### Xem danh sách sản phẩm

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Catalog sản phẩm của mọi vendor. |
| Actor | super_admin, admin |
| Trigger | Menu **All products**. |
| Main Flow | 1. Bảng: ảnh mockup, **Vendor**, **Code**, **Name**, **Material**, **Status**, **Fastway**, **Created**.<br>2. Mặc định 100 dòng/trang (20/50/100/200). |
| Alternative Flow | A1. Không có kết quả → "No products match your filters".<br>A2. Badge Fastway **Failed** → popup "Lỗi sync Fastway" chi tiết lỗi.<br>A3. Click dòng → mở drawer chi tiết. |
| Business Rule | **Bộ lọc:** tìm theo code hoặc name, Vendor, Status (Active / Inactive).<br>**Fastway sync status:** Synced / Pending / Failed / Chưa sync. |

### Xem chi tiết sản phẩm (drawer)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem thông tin & variant của 1 sản phẩm. |
| Actor | super_admin, admin |
| Trigger | Click 1 dòng sản phẩm. |
| Main Flow | 1. Header: mockup, tên, code; Vendor, Material, Status, Fastway, Created, Updated.<br>2. Tab **Thông tin**: danh sách **Variants (N)** có tìm kiếm + phân trang.<br>3. Tab **Lịch sử thay đổi**. |
| Alternative Flow | A1. **Sync to FW** → đẩy sản phẩm sang Fastway: "Đã enqueue N sản phẩm" hoặc "Sản phẩm đã được bỏ qua (skipped)"; lỗi → "Sync thất bại".<br>A2. **Sync from FF** → yêu cầu FF đẩy lại sản phẩm này. |
| Exception Flow | Sản phẩm không còn → "Sản phẩm không còn tồn tại", đóng drawer. |

### Sync sản phẩm từ FF

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Yêu cầu FF đẩy lại sản phẩm của 1 vendor hoặc tất cả vendor. |
| Actor | super_admin, admin |
| Trigger | Nút **Sync vendor từ FF** (khi đã lọc vendor) / **Sync tất cả từ FF**. |
| Main Flow | 1. Popup confirm.<br>2. Click **Sync**. |
| Post-conditions | Thành công: "Đã yêu cầu sync — sản phẩm sẽ cập nhật sau ít phút". Một phần lỗi: "Sync một phần: X/Y vendor OK, Z lỗi — xem audit log". Thất bại: "Yêu cầu sync thất bại". |

### Export sản phẩm

| Mục | Nội dung |
|---|---|
| Main Flow | **Export by filter (N)** (bắt buộc chọn vendor) / **Export selected (N)**. |
| Exception Flow | "Export thất bại". |

### Import thông số Fastway

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Upload Excel để cập nhật thông số Fastway (giá, mã…) cho variant. |
| Actor | super_admin, admin |
| Trigger | Nút **Import**. |
| Pre-conditions | Đã chọn 1 vendor ở filter (nếu chưa: nút disable, tooltip "Chọn vendor để import"). |
| Main Flow | 1. Kéo-thả hoặc **Chọn file .xlsx**.<br>2. Hệ thống phân tích (preview) → hiển thị danh sách thay đổi và lỗi.<br>3. Click **Apply (N)**. |
| Post-conditions | Thành công: "Đã apply X dòng, enqueue Y sản phẩm để sync", đóng popup. Thất bại: "Apply thất bại — vui lòng thử lại". |
| Alternative Flow | **Tải lại file** → về bước chọn file. |
| Exception Flow | E1. File > 5 MB → "File quá lớn — tối đa 5 MB".<br>E2. Không parse được → "Không thể phân tích file — hãy kiểm tra lại định dạng .xlsx".<br>E3. Preview có lỗi → nút **Apply** disable. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **File** * | Định dạng .xlsx | Không thể phân tích file — hãy kiểm tra lại định dạng .xlsx | — |
| **File** * | ≤ 5 MB | File quá lớn — tối đa 5 MB | — |
