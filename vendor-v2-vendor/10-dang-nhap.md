# Đăng nhập

Route: `/login` — Role: tất cả (chưa đăng nhập).

### Đăng nhập hệ thống

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | User đăng nhập bằng email + mật khẩu để vào Vendor Mini App. |
| Actor | Mọi user (owner, manager, production, shipping, viewer, staff PW, admin, super_admin) |
| Trigger | Mở `/login`, hoặc bị redirect về `/login` khi chưa đăng nhập / route không tồn tại. |
| Pre-conditions | Chưa đăng nhập. Nếu đã đăng nhập → tự redirect về trang mặc định theo role. |
| Post-conditions | Thành công: lưu token, xoá cache dữ liệu cũ, chuyển trang theo role. Thất bại: hiện thông báo lỗi đỏ trên form, giữ nguyên dữ liệu đã nhập. |
| Main Flow | 1. Màn hình hiển thị **Sign in** – "Sign in to manage orders, products, and vendors."<br>2. Nhập **Email**, **Mật khẩu** (Password).<br>3. Click **Gửi** (Submit) → nút disable + spinner trong lúc gửi.<br>4. Email được trim + chuyển chữ thường, mật khẩu được trim trước khi gửi.<br>5. Thành công → điều hướng:<br>- role **super_admin / admin** → `/admin`<br>- role khác → `/orders` |
| Exception Flow | E1. Sai thông tin / tài khoản bị khoá → hiện lỗi do API trả về (xem bảng dưới).<br>E2. HTTP 429 → "Too many attempts. Please try again shortly."<br>E3. HTTP ≥ 500 → "Server error. Please try again in a moment."<br>E4. Không kết nối được → "Unable to sign in. Please check your connection and try again."<br>E5. Lỗi không xác định → "Đăng nhập thất bại" / "Login failed". |
| Business Rule | - Nhãn field/nút theo ngôn ngữ đang chọn; tiêu đề "Sign in" và mô tả luôn tiếng Anh.<br>- Sau login, ngôn ngữ UI tự đổi theo `locale` của user.<br>- ⚠️ Message lỗi từ API được hiển thị nguyên văn; FE có bản dịch cho `invalid_credentials` ("Email hoặc mật khẩu không đúng" / "Email or password is incorrect") và `account_disabled` ("Tài khoản đã bị vô hiệu hoá" / "Account is disabled") nhưng màn login không gọi bản dịch → cần confirm BE trả code hay message.<br>- ⚠️ Không có giới hạn số lần sai / khoá tài khoản ở FE (chỉ xử lý HTTP 429 từ BE). |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Email** * | Trim, chuyển lowercase; bắt buộc; đúng định dạng email | Invalid email (message mặc định, chưa dịch) | Invalid email |
| **Email** * | ≤ 256 ký tự | String must contain at most 256 character(s) (chưa dịch) | String must contain at most 256 character(s) |
| **Mật khẩu** * | Trim; bắt buộc (≥ 1 ký tự sau trim) | String must contain at least 1 character(s) (chưa dịch) | String must contain at least 1 character(s) |
| **Mật khẩu** * | ≤ 256 ký tự | String must contain at most 256 character(s) (chưa dịch) | String must contain at most 256 character(s) |

> Ô Email là input `type=email` nên trình duyệt có thể chặn và hiện tooltip native trước khi validate của app chạy.
