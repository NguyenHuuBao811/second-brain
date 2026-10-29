# User của PW (Platform users)

Route: `/platform-users` — Role: **super_admin, admin** (role khác → "Forbidden"). Menu: nhóm **Quản trị** → **User PW**. Áp dụng [quy tắc validate mặc định](../vendor-v2-admin/00-README.md#quy-tắc-validate-mặc-định-cho-input).

### Xem danh sách tài khoản PW

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem các tài khoản cấp platform (Super admin, Admin, Staff). |
| Actor | super_admin, admin |
| Trigger | Vào menu **User PW**. |
| Main Flow | 1. Tiêu đề **User của PW** — "Quản lý tài khoản admin và staff cấp platform".<br>2. Bảng: avatar, **Người dùng** (username + email), **Vai trò** (Super admin / Admin / Staff), **Trạng thái** (Hoạt động / Đã khoá), **Người tạo** ("—" nếu không có), **Ngày tạo**, menu thao tác. |
| Alternative Flow | Chưa có tài khoản → "Chưa có tài khoản nào" + nút **Tài khoản mới**. |
| Business Rule | - Dòng có role **Super admin** và dòng của **chính mình** không có menu thao tác.<br>- Không có tìm kiếm / lọc / phân trang. |

### Tạo tài khoản PW

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Tạo tài khoản Admin hoặc Staff. |
| Actor | super_admin, admin |
| Trigger | Click **Tài khoản mới**. |
| Post-conditions | Thành công: "Đã tạo tài khoản", đóng popup, reset form. Thất bại: lỗi từ server hoặc "Tạo tài khoản thất bại". |
| Main Flow | 1. Popup **Tài khoản platform mới**: **Tên đăng nhập**, **Mật khẩu**, **Email**, **Vai trò** (mặc định Staff).<br>2. Click **Tạo tài khoản**. |
| Alternative Flow | **Huỷ** → đóng popup. |
| Exception Flow | Server trả lỗi validate → toast liệt kê "<field>: <message>". |
| Business Rule | - Nút **Tạo tài khoản** disable khi thiếu Tên đăng nhập, Mật khẩu hoặc Email.<br>- Vai trò chỉ có **Admin** / **Staff** (không tạo được Super admin).<br>- Staff dùng để xử lý đơn của vendor self-managed ở 3 trạm Assize / Label / Shipping.<br>- ⚠️ Admin cũng tạo được Admin khác — cần confirm nghiệp vụ. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Tên đăng nhập** | Bắt buộc, trim, 1–128 ký tự, chỉ chữ, số và `. _ -`. | ⚠️ Message từ server, chưa có bản VI | "Username is required" / "Username must be at most 128 characters" / "Username may only contain letters, numbers, and . _ -" |
| **Mật khẩu** | Bắt buộc, trim, 8–256 ký tự. | ⚠️ như trên | "Password must be at least 8 characters" / "Password must be at most 256 characters" |
| **Email** | Bắt buộc, trim, chữ thường, đúng định dạng, ≤ 256 ký tự. | ⚠️ như trên | "Email is invalid" / "Email must be at most 256 characters" |
| **Vai trò** | admin / staff. | — | — |

### Đổi mật khẩu tài khoản PW

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Đặt mật khẩu mới cho 1 tài khoản Admin/Staff. |
| Actor | super_admin, admin |
| Trigger | Menu thao tác → **Đổi mật khẩu**. |
| Post-conditions | Thành công: "Đã lưu thay đổi", đóng popup. Thất bại: lỗi server hoặc "Cập nhật thất bại". |
| Main Flow | 1. Popup **Đổi mật khẩu — <username>**, ô **Mật khẩu mới**.<br>2. Click **Lưu mật khẩu**. |
| Alternative Flow | **Huỷ** → đóng. |
| Business Rule | Nút **Lưu mật khẩu** disable khi ô trống. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Mật khẩu mới** | Bắt buộc, 8–256 ký tự (schema). | ⚠️ Message từ server / "Cập nhật thất bại" | "Update failed" |

### Khoá / Mở khoá tài khoản PW

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Khoá hoặc mở khoá tài khoản Admin/Staff. |
| Actor | super_admin, admin |
| Trigger | Menu thao tác → **Khoá** (đang Hoạt động) / **Mở khoá** (đang Đã khoá). |
| Post-conditions | "Đã khoá tài khoản" / "Đã mở khoá tài khoản". Thất bại: lỗi server hoặc "Cập nhật thất bại". |
| Main Flow | Click → đổi trạng thái ngay, không có confirm. |
| Business Rule | Không áp dụng cho Super admin và chính mình (không có menu). |
