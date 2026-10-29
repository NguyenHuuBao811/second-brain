# Cài đặt Vendor

Route: `/vendor/settings` — Role-permission: menu hiện khi có `vendors.settings` (mặc định chỉ **owner**). ⚠️ Route không có guard permission trên FE (vào bằng URL vẫn render), chặn dựa vào backend.

Text màn này chỉ có tiếng Anh.

### Cập nhật mặc định của Vendor

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Đặt ngôn ngữ và theme mặc định cho vendor. |
| Actor | owner |
| Trigger | Click **Save changes** trong card **Defaults**. |
| Pre-conditions | Đã tải được thông tin vendor. |
| Post-conditions | Thành công: toast "Settings saved". Thất bại: "Save failed". |
| Main Flow | 1. Tiêu đề **Vendor settings** — "Configure your vendor's identity and defaults".<br>2. Card **Defaults** — "Locale and theme preferences for this vendor".<br>3. Chọn **Default locale**: **Vietnamese (VI)** / **English (EN)**.<br>4. Chọn **Default theme**: **Light** / **Dark** / **System**.<br>5. Click **Save changes** (đang lưu → "Saving…"). |
| Business Rule | - Giá trị ban đầu lấy từ cấu hình vendor hiện tại.<br>- Chỉ nhận locale `vi`/`en`, theme `light`/`dark`/`system`; không nhận field khác.<br>- ⚠️ Chưa xác minh mặc định vendor áp dụng thế nào cho user (user mới? user chưa chọn?) — cần dev confirm.<br>- Màn không có phần chỉnh "identity" dù subtitle có nhắc. |
