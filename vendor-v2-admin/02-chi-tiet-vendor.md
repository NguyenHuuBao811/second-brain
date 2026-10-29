# Chi tiết Vendor

Route: `/admin/vendors/:id` — Role: super_admin, admin. Áp dụng [quy tắc validate mặc định](00-README.md#quy-tắc-validate-mặc-định-cho-input).

Header: tên vendor, code, badge status, nút **Suspend**/**Activate** (xem [01](01-quan-ly-vendor.md#suspend--activate-vendor)). 2 tab: **Overview**, **Users**.
Vendor không tồn tại → "Vendor not found" + nút **Back to vendors**.

### Xem thông tin Vendor (tab Overview)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem metadata vendor và liên kết FF supplier. |
| Actor | super_admin, admin |
| Trigger | Mở trang chi tiết vendor. |
| Main Flow | Hiển thị 4 card:<br>1. **Vendor metadata**: ID, Name, Code, Status, Created.<br>2. **FF Supplier link** (badge Locked): Supplier, Supplier code, FF id (nút copy), Linked at.<br>3. **Cấu hình sản xuất** (xem UC dưới).<br>4. **API access** (xem UC dưới). |
| Business Rule | FF Supplier link không sửa được: "To change supplier, delete and recreate this vendor." |

### Đổi luồng sản xuất (Cấu hình sản xuất)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Chọn 1 trong 3 luồng sản xuất cho vendor. |
| Actor | super_admin, admin |
| Trigger | Chọn radio khác luồng hiện tại. |
| Pre-conditions | Vendor tồn tại. |
| Post-conditions | Thành công: toast "Đã cập nhật sub-barcode" / "Đã cập nhật". Thất bại: "Cập nhật thất bại". |
| Main Flow | 1. Chọn luồng mới.<br>2. Hệ thống mở popup confirm tương ứng, hiển thị số đơn/unit bị ảnh hưởng.<br>3. Click xác nhận → lưu. |
| Alternative Flow | A1. **Huỷ** → giữ nguyên luồng cũ.<br>A2. Icon lịch sử → popup **Lịch sử đổi luồng sản xuất** (gộp cả 2 công tắc theo thời gian). |
| Exception Flow | `vendor_flow_conflict` → "Không bật được cùng lúc với luồng sub-barcode. Tắt luồng kia trước." |
| Business Rule | **3 luồng (loại trừ nhau):**<br>- **Sản xuất theo mã đơn** (mặc định): quét mã đơn ở 3 trạm Assize / Label / Shipping.<br>- **Sản xuất theo Sub-barcode**: bật cấu hình workflow theo product group + trạm scan sản xuất. Hiển thị "Bật lúc …" / "Chưa từng bật".<br>- **Vendor dùng hệ thống riêng** (self-managed): nhân sự PW (role Staff) xử lý đơn ở 3 trạm.<br><br>**Bật Sub-barcode:** chỉ item FF đẩy xuống SAU khi bật mới có workflow tuỳ chỉnh. Màn cấu hình (Nhóm sản phẩm, Phụ kiện, Partner) mở ngay; trạm quét hiện khi đã cấu hình workflow. Hiện số đơn chưa xuất xưởng (giữ workflow mặc định). Nếu đang self-managed → bật sub-barcode đồng thời TẮT self-managed; đơn đã thuộc PW vẫn do staff làm nốt.<br><br>**Tắt Sub-barcode:** item mới chỉ có workflow mặc định. Unit đang dở vẫn quét được; trạm quét, Barcodes, Lỗi sản xuất tự ẩn khi unit cuối xong. Màn cấu hình ẩn ngay. Hiện số unit chưa quét xong.<br><br>**Bật self-managed:** đơn tạo TỪ LÚC BẬT thuộc về nhân sự PW, vendor không thấy nữa. Đơn cũ vẫn ở phía vendor.<br>**Tắt self-managed:** chỉ ngừng nhận đơn mới; đơn đã về PW vẫn do staff làm nốt. |

### Cấu hình API access

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Bật/tắt API, đặt thời hạn và tạo/rotate API key cho vendor. |
| Actor | super_admin, admin |
| Trigger | Thao tác trong card **API access**. |
| Main Flow | 1. Bật/tắt **Bật API**.<br>2. Chọn **Thời hạn**: 30 ngày / 90 ngày (mặc định) / 365 ngày / Ngày cụ thể / Không hết hạn.<br>3. Click **Lưu** → "Đã lưu cấu hình API".<br>4. Click **Tạo key** (chưa có key) → popup **API key mới** hiển thị key + nút **Copy**. |
| Alternative Flow | A1. Đã có key → **Tạo lại key** → confirm "Tạo lại API key?" (key cũ ngừng hoạt động ngay) → **Xác nhận**.<br>A2. **Xem API docs** → mở `/api-docs?vendor=<id>`. |
| Exception Flow | E1. Có thay đổi chưa lưu → nút tạo key disable + "Lưu cấu hình trước khi tạo key".<br>E2. Tạo key khi API đang tắt → cảnh báo "API đang tắt — key này chưa dùng được cho tới khi bạn bật API và lưu." |
| Business Rule | - Key **chỉ hiển thị 1 lần**, đóng popup không xem lại được.<br>- Dòng trạng thái: "Key …<4 số cuối>" / "Chưa tạo key"; "Hết hạn <ngày>" / "Không hết hạn"; badge "Đã hết hạn"; "Dùng lần cuối <ngày>" / "Chưa dùng".<br>- Thời hạn preset tính từ thời điểm lưu; Ngày cụ thể hết hạn lúc 23:59:59 (GMT+7) ngày đó. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Ngày cụ thể** | Bắt buộc khi chọn preset Ngày cụ thể; ≥ ngày hôm nay (GMT+7) | (Nút **Lưu** disable) | — |

### Thêm user (tab Users)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Tạo owner (lần đầu) hoặc user bổ sung cho vendor. |
| Actor | super_admin, admin |
| Trigger | Click **Add owner** (vendor chưa có owner) hoặc **Add user**. |
| Post-conditions | Thành công: "Owner created" / "User created", đóng popup. Thất bại: hiển thị lỗi từ API hoặc "Create user failed". |
| Main Flow | 1. Mở popup.<br>2. Nhập **Username**, **Email**, **Password**; (Add user) chọn **Role**.<br>3. Click **Create owner** / **Create user**. |
| Business Rule | - Mỗi vendor có đúng 1 owner; phải tạo owner trước khi thêm staff khác.<br>- Role cho user thường: manager (mặc định), production, shipping, viewer.<br>- Bảng user: **Username** (badge owner), **Email**, **Role**, **Status**, **Created**, menu **Reset password**. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Username** * | Bắt buộc | (Nút tạo disable) | — |
| **Email** * | Bắt buộc, input type email | (Nút tạo disable) | — |
| **Password** * | Bắt buộc. ⚠️ FE không check độ dài — rule do BE | (Nút tạo disable) | — |
| **Role** * | Chỉ khi Add user; 1 trong manager/production/shipping/viewer | — | — |

### Reset password user

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Admin đặt mật khẩu mới cho user vendor. |
| Actor | super_admin, admin |
| Trigger | Menu ⋯ của user → **Reset password**. |
| Main Flow | 1. Nhập **New password**, **Confirm password**.<br>2. Click **Reset password** (hoặc Enter ở ô confirm). |
| Post-conditions | Thành công: "Password reset for <username>". Thất bại: "Reset failed". |
| Business Rule | Admin tự chuyển mật khẩu cho user qua kênh bảo mật. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **New password** * | ≥ 8 ký tự | — | Min 8 characters. |
| **Confirm password** * | Trùng New password | — | Passwords do not match. |
