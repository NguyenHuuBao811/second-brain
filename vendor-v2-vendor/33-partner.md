# Partner

Route: `/partners` — Menu hiển thị với permission `partners.manage` (owner, manager).
Điều kiện: vendor đã bật **Sub-barcode** (nếu chưa → chuyển về `/orders`).

### Xem danh sách partner

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Danh sách partner (seller) được đồng bộ từ FF và số product đã gán riêng. |
| Actor | owner, manager |
| Trigger | Menu **Partner**. |
| Main Flow | 1. Ô tìm "Tìm theo code" (tối đa 100 ký tự, debounce 300ms).<br>2. Bảng: **Seller ID**, **Products custom** ("N products"), nút **View details**.<br>3. Phân trang 10/20/50 (mặc định 10). |
| Alternative Flow | Không có dữ liệu → "Chưa có partner nào được đồng bộ". |
| Business Rule | Vendor không tạo/xóa partner; partner đến từ FF. ⚠️ Nút **Sync toàn bộ partner** chỉ có ở màn admin, vendor không có. |

### Xem chi tiết partner

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem các product đã gán cho partner. |
| Actor | owner, manager |
| Trigger | **View details**. |
| Main Flow | 1. Drawer tiêu đề = Seller ID, nút **Add product**.<br>2. Bảng **Product name**, **Product code**, icon xóa.<br>3. Phân trang 10/20/50. |
| Alternative Flow | Chưa có product → "Partner này chưa có product nào". Click 1 product → mở drawer SKU. |

### Gán product cho partner

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Thêm product của vendor vào danh sách custom của partner. |
| Actor | owner, manager |
| Trigger | **Add product** trong drawer partner. |
| Main Flow | 1. Popup "Thêm product cho partner": ô "Tìm theo tên hoặc mã product" (debounce 300ms).<br>2. Danh sách tối đa 20 product (đã loại product đã gán).<br>3. Click **Thêm** ở dòng product. |
| Post-conditions | "Đã thêm product", đóng popup. |
| Alternative Flow | Không có kết quả → "Không tìm thấy product". |
| Exception Flow | "Product này đã được gán cho partner"; lỗi khác → "Có lỗi xảy ra". |
| Business Rule | Mỗi product chỉ gán 1 lần cho 1 partner. ⚠️ Việc loại trừ product đã gán trên UI chỉ dựa trên 100 product đầu của partner. |

### Bỏ product khỏi partner

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Gỡ product khỏi partner. |
| Actor | owner, manager |
| Trigger | Icon xóa (**Bỏ product khỏi partner**) trên dòng product. |
| Main Flow | 1. Click icon → xóa ngay (không có popup xác nhận). |
| Post-conditions | "Đã bỏ product". |
| Exception Flow | Lỗi → message từ server hoặc "Có lỗi xảy ra". |
| Business Rule | ⚠️ Phụ kiện đã gán cho SKU của product này có bị xóa theo hay không chưa xác minh. |

### Gán phụ kiện cho SKU

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Chọn phụ kiện áp cho từng SKU (variant) của product đã gán cho partner. |
| Actor | owner, manager |
| Trigger | Click product trong drawer partner → drawer SKU → nút **+** (**Add Accessories**). |
| Main Flow | 1. Drawer SKU: bảng **Sku**, **Accessories** (chip tên phụ kiện), nút **+**; phân trang 10/20/50.<br>2. Popup "Phụ kiện cho sku" — "Tick phụ kiện áp cho sku này. Lưu sẽ thay thế toàn bộ danh sách hiện tại."<br>3. Tìm "Tìm theo tên hoặc mã phụ kiện"; tick checkbox (**Name**, **Code**); vùng **Đã chọn (N)** với **Bỏ hết** / bỏ từng chip.<br>4. **Lưu**. |
| Post-conditions | "Đã lưu phụ kiện"; danh sách phụ kiện của SKU được thay thế hoàn toàn. |
| Alternative Flow | A1. Bỏ nhanh 1 phụ kiện: icon ✕ trên chip trong bảng SKU (**Bỏ phụ kiện**) → lưu ngay.<br>A2. Vendor chưa có phụ kiện → "Vendor chưa khai phụ kiện nào"; tìm không ra → "Không tìm thấy phụ kiện".<br>A3. **Huỷ** → đóng, không lưu.<br>A4. Product chưa có SKU → "Product này chưa có sku nào". |
| Exception Flow | "Sku không thuộc product đang chọn"; "Phụ kiện không thuộc nhà cung cấp này"; lỗi khác → "Có lỗi xảy ra". |
| Business Rule | Popup chỉ hiển thị tối đa 100 phụ kiện mỗi lần tìm. Tối đa 50 phụ kiện / SKU (schema). |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Accessories** | ≤ 50 phụ kiện / SKU | ⚠️ không có message riêng | — |
| **Accessories** | Phụ kiện phải thuộc vendor | Phụ kiện không thuộc nhà cung cấp này | This accessory doesn't belong to this vendor |
| **Sku** | Thuộc product đang chọn | Sku không thuộc product đang chọn | This sku doesn't belong to the selected product |
| **Product** | Chưa gán cho partner | Product này đã được gán cho partner | This product is already assigned to the partner |
