# Lỗi sản xuất

Route: `/production-errors` (`?tab=errors|types`) — Chỉ vào được khi vendor có trạm sản xuất sub-barcode đang mở, ngược lại redirect **/orders**. Menu **Catalog › Lỗi sản xuất**: permission `production_errors.manage` (owner, manager). ⚠️ Route không check permission ở FE — user không có quyền gõ URL vẫn vào được trang, BE quyết định.

Tiêu đề **Lỗi sản xuất**, 2 tab: **Lỗi sản xuất** (mặc định), **Loại lỗi**. Nút góc phải đổi theo tab: **Thêm lỗi** / **Thêm loại lỗi**.
Danh mục này cấp lựa chọn **Error name** khi QC fail (xem [23](23-tram-san-xuat-sub-barcode.md#qc-fail-báo-lỗi-qc)).

### Xem danh sách lỗi sản xuất

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Tra cứu danh mục lỗi sản xuất. |
| Actor | owner, manager |
| Trigger | Mở tab **Lỗi sản xuất**. |
| Main Flow | 1. Tìm "Tìm theo tên lỗi" (debounce 300ms).<br>2. Lọc **Tất cả loại lỗi**, **Tất cả trạng thái** (Đang dùng / Ngừng dùng).<br>3. Bảng: **Tên lỗi**, **Mã lỗi** (copy), **Loại lỗi**, **Áp dụng cho bước** (tối đa 3, dư → "…"), **Mô tả**, **Ngày tạo**, **Trạng thái**, **Thao tác** (icon **Sửa**).<br>4. Phân trang 10/20/50. |
| Business Rule | Trống → "Chưa có lỗi sản xuất nào". |

### Thêm / sửa lỗi sản xuất

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Tạo hoặc chỉnh lỗi trong danh mục. |
| Actor | owner, manager (`production_errors.manage`) |
| Trigger | **Thêm lỗi** hoặc icon **Sửa** trên dòng. |
| Post-conditions | Toast "Đã tạo" / "Đã lưu"; đóng popup. |
| Main Flow | 1. Popup **Thêm lỗi sản xuất** / **Sửa lỗi sản xuất**.<br>2. Nhập **Tên lỗi**, chọn **Loại lỗi** ("Chọn loại lỗi..."), tick **Áp dụng cho bước** (Print, Cut, QC, Package), nhập **Mô tả**.<br>3. (Sửa) **Mã lỗi** read-only – "Mã sinh tự động từ tên và không đổi khi đổi tên"; **Trạng thái** Đang dùng / Ngừng dùng.<br>4. Click **Lưu**. |
| Alternative Flow | A1. **Huỷ** → đóng. |
| Exception Flow | `production_error_name_conflict` → "Tên lỗi đã tồn tại"; `production_error_type_not_found` → "Không tìm thấy loại lỗi"; `production_error_not_found` → "Không tìm thấy lỗi sản xuất"; khác → message API hoặc "Có lỗi xảy ra". |
| Business Rule | - Dropdown Loại lỗi chỉ gồm loại **Đang dùng** (khi sửa giữ thêm loại hiện tại).<br>- Chọn loại "Khác" → hint 'Loại này là loại "Khác" — thợ sẽ phải nhập mô tả khi chọn lỗi này lúc QC fail'.<br>- Lỗi **Ngừng dùng** không hiện ở QC fail. Khi tạo mới, trạng thái mặc định Đang dùng. Mô tả rỗng khi sửa → xoá mô tả. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Tên lỗi** * | Bắt buộc (trim), tối đa 50 ký tự, không trùng | (Nút Lưu disable) / Tên lỗi đã tồn tại | — / That error name already exists |
| **Loại lỗi** * | Bắt buộc | (Nút Lưu disable) | — |
| **Áp dụng cho bước** * | Chọn ≥ 1 công đoạn | Chọn ít nhất một công đoạn (hint, nút Lưu disable) | Pick at least one step |
| **Mô tả** | Tuỳ chọn, tối đa 255 ký tự | — | — |

### Xem / thêm / sửa loại lỗi

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Quản lý nhóm phân loại lỗi. |
| Actor | owner, manager (`production_errors.manage`) |
| Trigger | Tab **Loại lỗi** → **Thêm loại lỗi** hoặc icon **Sửa**. |
| Post-conditions | Toast "Đã tạo" / "Đã lưu". |
| Main Flow | 1. Bảng: **Tên loại lỗi** (badge **Hệ thống** cho loại "Khác"), **Số lỗi**, **Trạng thái**, **Thao tác**.<br>2. Popup **Thêm loại lỗi** / **Sửa loại lỗi**: **Tên loại lỗi**; (sửa) **Trạng thái**.<br>3. **Lưu**. |
| Exception Flow | `production_error_type_name_conflict` → "Tên loại lỗi đã tồn tại"; `production_error_type_system_locked` → 'Loại "Khác" là loại mặc định của hệ thống, không sửa được'. |
| Business Rule | Loại "Khác" (hệ thống) không có nút sửa. Trống → "Chưa có loại lỗi nào". ⚠️ Không có chức năng xoá lỗi/loại lỗi ở FE (chỉ Ngừng dùng). |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Tên loại lỗi** * | Bắt buộc (trim), tối đa 50 ký tự, không trùng | (Nút Lưu disable) / Tên loại lỗi đã tồn tại | — / That type name already exists |
