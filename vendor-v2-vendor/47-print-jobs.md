# Bàn in (Print jobs)

Route: `/print-jobs`, `/print-jobs/:id` — Role-permission: menu hiện khi có `print_boards.read` (mặc định owner, manager, production); super_admin/admin thấy ở nhóm **Quản trị**. ⚠️ Route không có guard permission trên FE — chặn dựa vào backend.

Job bàn in là dữ liệu nhận từ **Artwork Doctor (AD)**: mỗi job gồm các bàn in (board), dòng hàng (đơn/SKU) và sub-barcode trên từng bàn.

### Xem danh sách job bàn in

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Tra cứu các job bàn in vendor đã nhận. |
| Actor | owner, manager, production (super_admin/admin xem tất cả vendor) |
| Trigger | Vào menu **Bàn in**. |
| Main Flow | 1. Tiêu đề **Bàn in**.<br>2. Thanh lọc: ô tìm **Tìm theo mã job**, **Khoảng ngày** (mặc định 30 ngày gần nhất), tổng "<n> job".<br>3. Bảng: **Mã job** (copy được, badge **Có remake** nếu có, tên job bên dưới), **Quy trình**, **Số item**, **Số bàn in**, **Nguyên vật liệu** (badge), **Link bàn in** (icon mở tab mới), **Thời gian nhận** (+ badge đỏ "<n> dòng chưa khớp được đơn" nếu có).<br>4. Click dòng → chi tiết job. |
| Alternative Flow | A1. Không có job → "Chưa có job bàn in nào".<br>A2. super_admin/admin: thêm cột **Vendor** và lọc **Vendor** (**Tất cả vendor** / "<code> — <name>"). |
| Business Rule | - Tìm kiếm debounce 300ms; đổi filter → về trang 1.<br>- Khoảng ngày lọc theo thời gian nhận (00:00:00 → 23:59:59.999 UTC). ⚠️ Lọc theo UTC, không phải giờ VN — cần confirm.<br>- Phân trang server: 20 / 50 / 100 dòng/trang (mặc định 20).<br>- Filter **không** lưu trên URL. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Tìm theo mã job** | Tối đa 100 ký tự (cắt bớt khi nhập). | — | — |

### Xem chi tiết job bàn in

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem cấu trúc job: chất liệu → bàn in → sub-barcode, remake và dòng hàng. |
| Actor | owner, manager, production, super_admin, admin |
| Trigger | Click 1 job trong danh sách. |
| Main Flow | 1. Nút **Danh sách bàn in** (quay lại). Header **Chi tiết job**: mã job, tên, badge **Có remake**.<br>2. Khối thông tin: **Mã job**, **Vendor**, **Số item**, **Số chất liệu**, **Số bàn in**, **Quy trình**, **Thời gian nhận**, **Link bàn in**.<br>3. Có dòng chưa khớp đơn → cảnh báo đỏ "<n> dòng chưa khớp được đơn".<br>4. Tab **Chất liệu**: mỗi nhóm chất liệu (vd. "<material> <thickness>mm", hoặc "Chưa rõ chất liệu") hiện "<n> item · <n> file · <n> bàn in · <n> remake", mở rộng để xem:<br>- **Danh sách bàn in**: **Mã bàn**, **Tên bàn**, **Quy trình**, **Hình dạng**, **Kích thước**, **Hướng in** (Xuôi/Ngược), **Sub-barcode** (số lượng), **Số file**; mở rộng 1 bàn → **Sub-barcode trên bàn in** (mã, trạng thái, mã đơn, SKU, barcode).<br>- **Danh sách remake** (nếu có): Mã bàn, Tên bàn, Order ID, Mã barcode, **Lỗi**, **Lô gốc**, **Lớp in lại** ("<layer> ×<qty>").<br>- Khối **Không gắn bàn in**: sub-barcode không thuộc bàn nào.<br>5. Tab **Đơn hàng / SKU**: **Mã đơn** (badge Remake / **Chưa khớp**), **Sản phẩm**, **SKU**, **Số lượng**, **Mã barcode**, **Bàn in**, **Sub-barcode**. |
| Alternative Flow | A1. **Tải list sub-barcode** → tải file `print-job-<mã job>.xlsx`.<br>A2. Click mã đơn / sản phẩm / SKU / barcode → mở trang đơn, sản phẩm, item tương ứng.<br>A3. Job dựng tay không có bàn → "Job dựng tay — không có bàn in"; job chưa có bàn → "Job này chưa có bàn in nào"; không có dòng → "Job này chưa có dòng hàng nào"; bàn không có unit → "Bàn in này chưa có sub-barcode nào". |
| Exception Flow | E1. Không tìm thấy / lỗi tải → "Không tìm thấy job bàn in này".<br>E2. Tải file lỗi → toast "Tải list sub-barcode thất bại". |
| Business Rule | - Nếu chỉ có 1 nhóm chất liệu thì tự mở sẵn.<br>- Số item của nhóm = số sub-barcode khác nhau; nếu chưa có sub-barcode thì cộng số lượng dòng hàng.<br>- Dòng "Chưa khớp" = dòng từ AD chưa map được vào item đơn nào. |
