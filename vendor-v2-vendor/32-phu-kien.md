# Phụ kiện (Accessories)

Route: `/accessories` — Menu hiển thị với permission `accessories.manage` (owner, manager).
Điều kiện: vendor đã bật **Sub-barcode** (nếu chưa → chuyển về `/orders`).

### Xem danh sách phụ kiện

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Danh sách phụ kiện vendor đã khai báo (dùng để gán cho SKU của partner). |
| Actor | owner, manager |
| Trigger | Menu **Phụ kiện**. |
| Main Flow | 1. Ô tìm "Tìm theo tên hoặc mã phụ kiện" (tối đa 100 ký tự, debounce 300ms).<br>2. Bảng: **Tên phụ kiện**, **Mã phụ kiện** (có nút copy), **Ngày tạo**, **Thao tác** (icon sửa).<br>3. Phân trang 10/20/50 (mặc định 10). |
| Alternative Flow | Không có dữ liệu → "Chưa có phụ kiện nào". |
| Business Rule | ⚠️ Không có chức năng xóa phụ kiện trên UI. |

### Thêm phụ kiện

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Tạo phụ kiện mới. |
| Actor | owner, manager |
| Trigger | Nút **Thêm phụ kiện**. |
| Main Flow | 1. Popup "Thêm phụ kiện": nhập **Tên phụ kiện**.<br>2. Click **Lưu**. |
| Post-conditions | "Đã tạo". **Mã phụ kiện** do hệ thống sinh tự động. |
| Alternative Flow | **Huỷ** → đóng popup. |
| Exception Flow | "Tên phụ kiện đã tồn tại" / "Mã phụ kiện đã tồn tại" / "Đã hết dải mã phụ kiện của nhà cung cấp này"; lỗi khác → "Có lỗi xảy ra". |
| Business Rule | ⚠️ Quy tắc sinh mã (dải mã theo vendor) do backend quyết định, chưa xác minh định dạng. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Tên phụ kiện** * | Trim, 1–100 ký tự (rỗng → nút Lưu disable; input chặn > 100) | — | — |
| **Tên phụ kiện** * | Duy nhất trong vendor (backend) | Tên phụ kiện đã tồn tại | That accessory name already exists |

### Sửa phụ kiện

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Đổi tên phụ kiện. |
| Actor | owner, manager |
| Trigger | Icon sửa trên dòng. |
| Main Flow | 1. Popup "Sửa phụ kiện": **Tên phụ kiện** điền sẵn; **Mã phụ kiện** chỉ đọc ("Mã sinh tự động khi tạo, không sửa được").<br>2. **Lưu**. |
| Post-conditions | "Đã lưu". |
| Exception Flow | "Tên phụ kiện đã tồn tại"; không có thay đổi → "Không có thay đổi để lưu" ⚠️ (theo schema backend). |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Tên phụ kiện** * | Trim, 1–100 ký tự | — (nút Lưu disable) | — |
| **Tên phụ kiện** * | Duy nhất | Tên phụ kiện đã tồn tại | That accessory name already exists |
