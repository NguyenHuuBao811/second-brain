# Audit log

Route: `/admin/audit` — Role: super_admin, admin.

### Xem Audit log

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem dòng hoạt động cross-vendor. |
| Actor | super_admin, admin |
| Trigger | Menu **Audit log**. |
| Main Flow | 1. Mặc định lọc **7 ngày gần nhất** đến hiện tại.<br>2. Nhập filter → click **Apply**.<br>3. Bảng **Events**: **When**, **Vendor** (ID rút gọn, hover xem đầy đủ), **Actor** (username + role), **Action**, **Resource** (type / id). |
| Alternative Flow | Không có kết quả → "No audit events — Try adjusting your filters or date range". |
| Business Rule | - Filter chỉ áp dụng khi bấm **Apply** (không tự động).<br>- Tối đa **200** event; đủ 200 → hiển thị "(limit 200)". Không có phân trang.<br>- Filter lưu trên URL. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Vendor ID** | Optional; uuid hoặc code | — | — |
| **User ID** | Optional; uuid | — | — |
| **Action** | Optional; vd `order.create` (khớp chính xác ⚠️ cần confirm) | — | — |
| **From** | datetime-local | — | — |
| **To** | datetime-local. ⚠️ FE không check From ≤ To | — | — |
