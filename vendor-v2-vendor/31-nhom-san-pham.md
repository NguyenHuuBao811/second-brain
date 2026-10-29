# Nhóm sản phẩm (Product groups)

Route: `/product-groups`, `/product-groups/new`, `/product-groups/:id/edit`.
Điều kiện: vendor đã bật **Sub-barcode** (nếu chưa → chuyển về `/orders`). Menu hiển thị với permission `products.read` (owner, manager, shipping, viewer).
Tạo/sửa nhóm: `product_groups.manage` (owner, manager). Xem lịch sử Sub-barcode: `audit_logs.view` (owner, manager).

### Xem danh sách nhóm sản phẩm

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem các nhóm sản xuất và quy trình (workflow) của từng nhóm. |
| Actor | owner, manager, shipping, viewer |
| Trigger | Menu **Quản lý Nhóm sản phẩm**. |
| Pre-conditions | Vendor đã bật Sub-barcode. |
| Main Flow | 1. Ô tìm "Tìm kiếm theo tên nhóm hoặc mã..." (debounce 300ms).<br>2. Thẻ **Xử lý đơn hàng theo:** **Sub-barcode** — badge **Đang bật / Đang tắt** (tooltip "Chỉ admin Printway thay đổi được cài đặt này").<br>3. Bảng: **Tên nhóm sản xuất**, **Mã nhóm**, **Sản phẩm** (vài tên + "+N"; nhóm mặc định: "Tất cả sản phẩm chưa gán"), **Loại** (Mặc định / Thường), **Quy trình sản xuất** (các bước tùy chỉnh → Assize → Label → Shipping), **Ngày tạo**, **Thao tác** (**Sửa**). |
| Alternative Flow | A1. Không có nhóm → "Chưa có nhóm sản phẩm nào".<br>A2. Icon **Lịch sử bật/tắt** (cần `audit_logs.view`) → popup "Lịch sử Sub-barcode": danh sách Bật/Tắt + thời gian + người thực hiện (Super admin / Admin Printway); rỗng → "Chưa có thay đổi nào". |
| Business Rule | Nút **Tạo nhóm** và **Sửa** chỉ hiện với `product_groups.manage`; nếu Sub-barcode đang tắt thì disable, tooltip "Bật Sub-barcode để cấu hình". Vendor không tự bật/tắt Sub-barcode được. |

### Tạo nhóm sản phẩm

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Tạo nhóm sản xuất, gán sản phẩm và thiết lập quy trình. |
| Actor | owner, manager (`product_groups.manage`) |
| Trigger | Nút **Tạo nhóm** → `/product-groups/new`. |
| Pre-conditions | Sub-barcode đang bật. |
| Main Flow | 1. **Thông tin nhóm**: **Tên nhóm sản xuất** *, **Mã nhóm sản xuất** * (tự in hoa), **Sản phẩm áp dụng** (chọn từ dropdown, hiển thị dạng chip, có nút xóa).<br>2. **Quy trình sản xuất**: chọn **Thêm công đoạn tùy chỉnh** (Print / Cut / QC / Package); mỗi bước có tên cố định theo loại + **Mô tả ngắn (tùy chọn)**; sắp xếp bằng kéo-thả hoặc nút **Lên trên / Xuống dưới**; **Xoá công đoạn**.<br>3. 3 bước cuối **Assize, Label, Shipping** luôn cố định ("Bắt buộc").<br>4. Click **Tạo nhóm sản xuất**. |
| Post-conditions | "Đã tạo nhóm sản phẩm", quay về danh sách. Đơn hàng của các sản phẩm được gán sẽ áp dụng quy trình nhóm này. |
| Alternative Flow | A1. Sản phẩm đang thuộc nhóm khác → chip hiển thị "(sẽ chuyển từ nhóm X)"; khi lưu sản phẩm chuyển sang nhóm mới.<br>A2. **Hủy bỏ** / mũi tên **Quay lại** → về danh sách. |
| Exception Flow | Lỗi validate → toast message tương ứng (bảng dưới). Lỗi server: "Mã nhóm đã tồn tại", "Danh sách sản phẩm không hợp lệ", "Cần bật Sub-barcode trước khi cấu hình nhóm sản phẩm". |
| Business Rule | Danh sách chọn sản phẩm lấy tối đa 200 sản phẩm đầu (bỏ sản phẩm đã xóa) — ⚠️ vendor > 200 sản phẩm có thể không thấy hết. Một sản phẩm chỉ thuộc 1 nhóm. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Tên nhóm sản xuất** * | Trim, 1–128 ký tự | Tên nhóm không hợp lệ (1–128 ký tự). | Invalid group name (1–128 characters). |
| **Mã nhóm sản xuất** * | Chữ in hoa/số/gạch ngang, bắt đầu bằng chữ hoặc số, 2–32 ký tự | Mã nhóm không hợp lệ. Chỉ dùng chữ in hoa, số và dấu gạch ngang (2–32 ký tự). | Invalid group code. Use uppercase letters, digits and dashes only (2–32 characters). |
| **Mã nhóm sản xuất** * | Duy nhất (backend) | Mã nhóm đã tồn tại | Group code already exists |
| **Quy trình sản xuất** | ≤ 20 bước tùy chỉnh; mô tả ≤ 256 ký tự; không trùng bước | Danh sách công đoạn không hợp lệ. Mỗi công đoạn cần tên (tối đa 64 ký tự) và không được trùng. | Invalid workflow steps. Each step needs a name (max 64 characters) and must be unique. |
| **Sản phẩm áp dụng** | ≤ 1000 sản phẩm | Danh sách sản phẩm áp dụng không hợp lệ. | Invalid list of applicable products. |
| Khác | — | Thông tin nhập vào không hợp lệ. Vui lòng kiểm tra lại. | The information entered is invalid. Please check again. |

### Sửa nhóm sản phẩm

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Cập nhật tên, quy trình và sản phẩm của nhóm. |
| Actor | owner, manager (`product_groups.manage`) |
| Trigger | **Sửa** trên dòng nhóm → `/product-groups/:id/edit`. |
| Pre-conditions | Sub-barcode đang bật. |
| Main Flow | 1. Form điền sẵn dữ liệu; **Mã nhóm sản xuất (Không thể sửa)** bị khóa ("Mã nhóm là duy nhất định danh và không thể thay đổi sau khi khởi tạo.").<br>2. Sửa tên / quy trình / sản phẩm.<br>3. **Lưu thay đổi**. |
| Post-conditions | "Đã cập nhật nhóm sản phẩm", về danh sách. |
| Alternative Flow | Nhóm **Mặc định**: không có ô chọn sản phẩm, chỉ hiện "Nhóm mặc định gồm mọi sản phẩm chưa được gán nhóm khác." |
| Exception Flow | "Không thể gán sản phẩm trực tiếp cho nhóm mặc định"; các lỗi validate như khi tạo. |
| Business Rule | Danh sách sản phẩm chỉ gửi lên khi user có thay đổi phần sản phẩm. ⚠️ Không có chức năng xóa nhóm trên UI. ⚠️ Ảnh hưởng tới đơn đang sản xuất khi đổi quy trình chưa xác minh. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Tên nhóm sản xuất** * | Trim, 1–128 ký tự | Tên nhóm không hợp lệ (1–128 ký tự). | Invalid group name (1–128 characters). |
| **Quy trình sản xuất** | ≤ 20 bước; mô tả ≤ 256 ký tự | Danh sách công đoạn không hợp lệ. Mỗi công đoạn cần tên (tối đa 64 ký tự) và không được trùng. | Invalid workflow steps. Each step needs a name (max 64 characters) and must be unique. |
| **Sản phẩm áp dụng** | ≤ 1000; không áp cho nhóm mặc định | Không thể gán sản phẩm trực tiếp cho nhóm mặc định | Cannot assign products directly to the default group |
