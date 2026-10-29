# Tài khoản (Account)

Route: `/account` — Role: mọi user đã đăng nhập (vào từ dropdown user ở header → **Account**). Áp dụng [quy tắc validate mặc định](../vendor-v2-admin/00-README.md#quy-tắc-validate-mặc-định-cho-input).

Trang gồm 3 card: thông tin user (username, role · mã vendor), **Preferences**, **Security**. Toàn bộ text trang này chỉ có tiếng Anh (chưa dịch VI).

### Cập nhật Preferences (ngôn ngữ, theme)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | User chọn ngôn ngữ hiển thị và giao diện màu, lưu vào tài khoản. |
| Actor | Mọi user đã đăng nhập |
| Trigger | Click **Save preferences**. |
| Pre-conditions | Đã đăng nhập. |
| Post-conditions | Thành công: toast "Preferences saved"; ngôn ngữ & theme áp dụng ngay. Thất bại: "Save failed". |
| Main Flow | 1. Chọn **Locale**: **Vietnamese (VI)** / **English (EN)** (mặc định = locale của tài khoản, không có thì VI).<br>2. Chọn **Theme**: **Light** / **Dark** / **System** (mặc định = theme đang dùng trên trình duyệt).<br>3. Click **Save preferences** → hệ thống lưu locale, đổi ngôn ngữ app, rồi lưu theme. |
| Exception Flow | Lỗi khi lưu → toast "Save failed". Đang lưu → nút đổi thành "Saving…" và disable. |
| Business Rule | - Locale chỉ nhận `vi`, `en`; theme chỉ nhận `light`, `dark`, `system`.<br>- **System** = theo cài đặt sáng/tối của hệ điều hành.<br>- Locale và theme được lưu bằng 2 request riêng; ⚠️ nếu request thứ 2 lỗi thì locale đã lưu nhưng theme chưa. |

### Đổi mật khẩu

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | User tự đổi mật khẩu đăng nhập. |
| Actor | Mọi user đã đăng nhập |
| Trigger | Click **Update password** trong card **Security**. |
| Pre-conditions | Đã nhập **New password** và **Confirm new password** trùng nhau. |
| Post-conditions | Thành công: toast "Password updated", 2 ô được xoá trống, thông tin user được tải lại. Thất bại: "Update failed". |
| Main Flow | 1. Nhập **New password**.<br>2. Nhập lại ở **Confirm new password**.<br>3. Click **Update password** → lưu mật khẩu mới (kèm locale & theme đang chọn ở card Preferences). |
| Exception Flow | E1. Hai ô không khớp → hiện "Passwords do not match", nút disable.<br>E2. Backend từ chối (vd. < 8 ký tự) → toast "Update failed" (không hiện lý do cụ thể). |
| Business Rule | - Không yêu cầu nhập mật khẩu hiện tại.<br>- Nút **Update password** chỉ bật khi New password khác rỗng và trùng Confirm.<br>- Request đổi mật khẩu gửi kèm locale/theme đang chọn → ⚠️ có thể ghi đè preferences chưa bấm Save. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **New password** | Bắt buộc. 8–256 ký tự (rule schema; FE không check độ dài, backend trả lỗi). ⚠️ Không trim. | (UI chưa có bản VI) "Update failed" | "Update failed" |
| **Confirm new password** | Bắt buộc, phải trùng New password. | (UI chưa có bản VI) "Passwords do not match" | "Passwords do not match" |
