# Quản lý Vendor

Route: `/admin` — Role: super_admin, admin. Áp dụng [quy tắc validate mặc định](00-README.md#quy-tắc-validate-mặc-định-cho-input).

### Xem danh sách Vendor

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Admin xem toàn bộ vendor (multi-tenant) và số liệu tổng quan. |
| Actor | super_admin, admin |
| Trigger | Truy cập **/admin** (menu **Vendors**). |
| Pre-conditions | Đã đăng nhập, role hợp lệ. |
| Post-conditions | Thành công: hiển thị danh sách. Thất bại: hiển thị trạng thái rỗng / Forbidden. |
| Main Flow | 1. Hệ thống tải danh sách vendor.<br>2. Hiển thị 3 thẻ thống kê: **Total vendors**, **Active**, **Suspended**.<br>3. Hiển thị bảng: **Code**, **Name**, **Supplier**, **Status**, **Created**, menu hành động (⋯). |
| Alternative Flow | A1. Chưa có vendor → "No vendors yet" + nút **New vendor**.<br>A2. Click 1 dòng hoặc **View** → mở [Chi tiết vendor](02-chi-tiet-vendor.md). |
| Exception Flow | Đang tải → skeleton 4 dòng. |
| Business Rule | - Cột **Supplier** = `ffSupplierName (ffSupplierCodeAtLink)`; hover hiện FF id + thời điểm link.<br>- Menu ⋯: **View**, **Sync products từ FF**, **Suspend**/**Activate** (theo trạng thái hiện tại).<br>- Không có phân trang, tìm kiếm, filter. |

### Tạo mới Vendor

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Tạo vendor mới bằng cách link với 1 supplier bên FF. |
| Actor | super_admin, admin |
| Trigger | Click **New vendor**. |
| Pre-conditions | Có ít nhất 1 supplier trong cache chưa link vendor. |
| Post-conditions | Thành công: vendor tạo với status active, toast "Vendor created", đóng popup. Thất bại: giữ popup, toast lỗi. |
| Main Flow | 1. Mở popup **New vendor**.<br>2. Tìm & chọn supplier trong **Link to FF supplier** (tìm theo name / id / code).<br>3. Hệ thống tự điền **Vendor name**, **Internal code** từ supplier (read-only).<br>4. (Tuỳ chọn) nhập **Address**, bật **Chỉ mua label — Không sản xuất**.<br>5. Click **Create vendor**. |
| Alternative Flow | A1. Cache trống → hiện "No suppliers in cache yet" + nút **Đồng bộ từ FF**.<br>A2. Click **Đồng bộ từ FF** → gọi sync supplier, chờ ~2,5s, tải lại danh sách → toast "Đã kéo danh sách mới nhất từ FF".<br>A3. Click **Change** → bỏ chọn supplier, xoá name/code.<br>A4. **Cancel** / đóng popup → reset form. |
| Exception Flow | E1. Supplier vừa bị vendor khác link (`ff_supplier_already_linked`) → toast "Supplier was just linked to another vendor. Refreshing.", refresh list, bỏ chọn.<br>E2. Supplier không còn trên FF (`ff_supplier_not_found`) → toast "Supplier no longer exists in FF.", refresh, bỏ chọn.<br>E3. Lỗi khác → "Create failed".<br>E4. Sync supplier lỗi → "Đồng bộ suppliers thất bại". |
| Business Rule | - Chỉ liệt kê supplier **chưa** link vendor. Hết → "No available suppliers — all FF suppliers are already linked."<br>- Supplier không có code → không tạo được, báo lỗi dưới **Internal code**.<br>- Link supplier là **vĩnh viễn**; muốn đổi phải xoá & tạo lại vendor.<br>- **Self-managed** = vendor sản xuất trên hệ thống riêng; nhân sự PW chỉ nhập kích thước, mua label, xuất xưởng hộ.<br>- ⚠️ Field **Address** có trên form nhưng FE **không gửi** lên API (payload chỉ gồm name, code, ffSupplierId, selfManaged). |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Link to FF supplier** * | Bắt buộc chọn 1 supplier chưa link | (Nút **Create vendor** disable) | — |
| **Vendor name** * | Tự lấy từ supplier, không sửa | — | — |
| **Internal code** * | Tự lấy từ supplier; supplier phải có code | FF supplier chưa có code — không thể tạo vendor cho supplier này. Thêm code bên FF rồi sync lại. | — |
| **Address** | Optional, textarea | — | — |
| **Chỉ mua label — Không sản xuất** | Toggle, mặc định Off | — | — |

### Suspend / Activate Vendor

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Đổi trạng thái vendor giữa active ↔ suspended. |
| Actor | super_admin, admin |
| Trigger | Menu ⋯ → **Suspend** / **Activate** (hoặc nút trên trang chi tiết). |
| Pre-conditions | Vendor tồn tại. |
| Post-conditions | Thành công: toast "Vendor suspended" / "Vendor activated". Thất bại: "Update failed". |
| Main Flow | 1. Click hành động.<br>2. Hệ thống đổi status ngay (không có popup confirm). |
| Business Rule | ⚠️ Ảnh hưởng của suspended (user vendor còn login? đơn mới?) do backend xử lý — cần confirm. |

### Sync products từ FF (theo vendor)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Yêu cầu FF đẩy lại toàn bộ sản phẩm của 1 vendor. |
| Actor | super_admin, admin |
| Trigger | Menu ⋯ → **Sync products từ FF**. |
| Main Flow | 1. Popup confirm "Sync sản phẩm từ FF": FF sẽ đẩy lại sản phẩm của "<vendor>". Dữ liệu cập nhật sau ít phút.<br>2. Click **Sync**. |
| Post-conditions | Thành công: "Đã yêu cầu sync — sản phẩm sẽ cập nhật sau ít phút". Thất bại: "Yêu cầu sync thất bại". |
| Business Rule | Xử lý bất đồng bộ — dữ liệu về sau vài phút. |
