# Partners

Route: `/admin/partners` — Role: super_admin, admin.

### Xem danh sách Partner

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem danh sách partner (seller) đã đồng bộ từ FF. |
| Actor | super_admin, admin |
| Trigger | Menu **Partners**. |
| Main Flow | 1. Bảng 1 cột **Seller ID** (partner code).<br>2. Phân trang 10 / 20 / 50, mặc định 10. |
| Alternative Flow | Chưa có dữ liệu → "Chưa có partner nào được đồng bộ". |
| Business Rule | Tìm kiếm theo code, debounce 300ms. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Tìm theo code** | Tối đa 100 ký tự (chặn nhập) | — | — |

### Sync toàn bộ partner

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Yêu cầu FF đẩy lại toàn bộ partner. |
| Actor | super_admin, admin |
| Trigger | Nút **Sync toàn bộ partner**. |
| Main Flow | Click nút → gửi yêu cầu ngay (không confirm). |
| Post-conditions | Thành công: "Đã yêu cầu đồng bộ, FF sẽ đẩy dữ liệu về trong ít phút". Thất bại: hiện lỗi API (vd "Chưa cấu hình endpoint FF cho môi trường này", "Không kết nối được tới FF, thử lại sau"). |
