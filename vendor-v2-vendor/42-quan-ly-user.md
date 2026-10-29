# Quản lý User (vendor)

Route: `/users`, `/users/:id/permissions` — Role-permission: menu hiện khi có `users.manage` (mặc định chỉ **owner**). ⚠️ Route không có guard permission trên FE — truy cập URL trực tiếp vẫn render, việc chặn dựa vào backend. Áp dụng [quy tắc validate mặc định](../vendor-v2-admin/00-README.md#quy-tắc-validate-mặc-định-cho-input).

Toàn bộ text 2 màn này chỉ có tiếng Anh (chưa dịch VI), trừ tên/mô tả permission.

### Xem danh sách user

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem danh sách thành viên của vendor. |
| Actor | owner (user có `users.manage`) |
| Trigger | Vào menu **Users**. |
| Main Flow | 1. Tiêu đề **Users** — "Vendor team and per-user permissions".<br>2. Bảng: avatar, **User** (username + email), **Role** (badge màu), **Status**, **Owner** (tick xanh nếu là chủ vendor), **Created**, menu thao tác (**Edit**, **Permissions**, **Disable**/**Enable**). |
| Alternative Flow | Chưa có user → "No users yet" + nút **New user**. |
| Business Rule | Danh sách không có tìm kiếm / lọc / phân trang. |

### Tạo user

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Tạo tài khoản mới cho thành viên vendor. |
| Actor | owner |
| Trigger | Click **New user**. |
| Post-conditions | Thành công: toast "User created", đóng popup, form reset. Thất bại: toast lỗi từ server hoặc "Create user failed". |
| Main Flow | 1. Popup **New user** gồm **Username**, **Password**, **Email (optional)**, **Role** (mặc định production).<br>2. Click **Create user**. |
| Alternative Flow | **Cancel** → đóng popup. |
| Exception Flow | Server trả lỗi validate → toast hiển thị từng dòng "<field>: <message>". |
| Business Rule | - Nút **Create user** disable khi chưa nhập Username hoặc Password.<br>- Dropdown Role có: owner, manager, production, shipping, viewer. ⚠️ Schema chỉ cho tạo **manager / production / shipping / viewer** — chọn owner nhiều khả năng bị backend từ chối.<br>- ⚠️ UI ghi Email "optional" nhưng schema yêu cầu email hợp lệ — cần dev confirm. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Username** | Bắt buộc, trim, 1–128 ký tự, chỉ chữ, số và `. _ -`. | (chưa có bản VI) | "Username is required" / "Username must be at most 128 characters" / "Username may only contain letters, numbers, and . _ -" |
| **Password** | Bắt buộc, trim, 8–256 ký tự. | (chưa có bản VI) | "Password must be at least 8 characters" / "Password must be at most 256 characters" |
| **Email (optional)** | Trim, chuyển chữ thường, đúng định dạng email, ≤ 256 ký tự. ⚠️ Xem Business Rule. | (chưa có bản VI) | "Email is invalid" / "Email must be at most 256 characters" |
| **Role** | Một trong manager, production, shipping, viewer (theo schema). | (chưa có bản VI) | — |

### Sửa user

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Đổi role, trạng thái, hoặc đặt lại mật khẩu cho 1 user. |
| Actor | owner |
| Trigger | Menu thao tác → **Edit** (mở panel bên phải). |
| Post-conditions | Thành công: toast "Saved", đóng panel. Thất bại: "Save failed". |
| Main Flow | 1. Panel hiện avatar, username, email.<br>2. Sửa **Role**, **Status** (**Active**/**Disabled**), **Reset password** (placeholder "Leave blank to keep current").<br>3. Click **Save** → chỉ gửi các field có thay đổi. |
| Alternative Flow | A1. Không thay đổi gì → **Save** chỉ đóng panel.<br>A2. **Cancel** → đóng panel. |
| Business Rule | - User là **Owner** của vendor: Role bị khoá + "Vendor owner — role cannot be changed."<br>- Reset password để trống = giữ mật khẩu cũ.<br>- ⚠️ Dropdown Role vẫn có "owner" nhưng schema chỉ nhận manager/production/shipping/viewer. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Reset password** | Không bắt buộc; nếu nhập: 8–256 ký tự (schema). FE không check. | (chưa có bản VI) "Save failed" | "Save failed" |
| **Role** | manager / production / shipping / viewer. | (chưa có bản VI) "Save failed" | "Save failed" |
| **Status** | active / disabled. | — | — |

### Khoá / Mở khoá user

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Khoá nhanh hoặc mở khoá tài khoản. |
| Actor | owner |
| Trigger | Menu thao tác → **Disable** (user đang active) / **Enable** (user đang disabled). |
| Post-conditions | Thành công: "User disabled" / "User enabled". Thất bại: "Update failed". |
| Main Flow | 1. Click **Disable**/**Enable** → hệ thống đổi trạng thái ngay. |
| Business Rule | - Không có popup xác nhận.<br>- ⚠️ FE không chặn khoá Owner hay tự khoá chính mình — cần backend confirm. |

### Override permission theo user

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Cấp thêm (Grant) hoặc thu hồi (Deny) từng permission cho 1 user, khác với mặc định của role. |
| Actor | owner |
| Trigger | Menu thao tác → **Permissions** (→ `/users/:id/permissions`). |
| Post-conditions | Thành công: "Permissions saved". Thất bại: "Save failed". |
| Main Flow | 1. Header: nút **Users** (quay lại), tiêu đề **Permissions** + badge role.<br>2. Card **Permission overrides** — "Override role defaults on a per-user basis. "Default" inherits from the role."<br>3. Bảng nhóm theo danh mục (Đơn hàng, Sản phẩm, Webhooks, Vendor, Người dùng, Báo cáo, Audit log, Khác). Mỗi dòng: tên permission (icon ⓘ hiện mô tả) + key, **Role default** (✓ / —), 3 lựa chọn **—** (Default) / **Grant** / **Deny**, **Effective** (**YES**/**NO**).<br>4. Thanh dưới cùng: "No overrides — all permissions follow role defaults" hoặc "<n> override(s) active" + nút **Save permissions**. |
| Alternative Flow | User không tồn tại → "User not found". |
| Business Rule | - Effective = Grant → YES; Deny → NO; Default → theo role.<br>- Chỉ dòng Grant/Deny được lưu; Save ghi đè toàn bộ override cũ.<br>- Không hiển thị/không override được các permission cấp platform: `vendors.manage`, `system_settings.manage`, `admin.orders.resync`, `admin.orders.update_address`.<br>- Số override tối đa = tổng số permission.<br>- ⚠️ FE không chặn override cho Owner hoặc cho chính mình. |
