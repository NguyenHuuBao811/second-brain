# Báo cáo (Reports)

Route: `/reports` — Role-permission: `reports.view` (mặc định owner, manager, viewer). Thiếu quyền → "Forbidden". Menu: nhóm **Phân tích** → **Reports**.

### Xem báo cáo theo ngày

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Thống kê số đơn / unit theo từng ngày tạo đơn, theo trạng thái sản xuất – vận chuyển. |
| Actor | owner, manager, viewer |
| Trigger | Vào menu **Reports**. |
| Main Flow | 1. Tiêu đề **Báo cáo** — "Thống kê theo ngày tạo đơn".<br>2. Tab loại đơn: **Orders** (đơn thường) / **Orders FBA** (bulk) / **Sample Order** / **TikTok orders** (tiktok, tiktok_seller). Mặc định **Orders**.<br>3. Lọc **Partner** (mặc định **Tất cả partner**; danh sách lấy theo partner của vendor) và **Khoảng ngày** (mặc định 14 ngày gần nhất tính cả hôm nay).<br>4. Bảng: cột **Day** + 18 cột chỉ số (bảng dưới); dòng **Tổng** ở đầu bảng. |
| Alternative Flow | A1. Không có dữ liệu → "Không có dữ liệu".<br>A2. Click số trong ô → mở danh sách đã lọc sẵn (theo ngày, loại đơn, partner): cột cấp đơn → `/orders`; cột cấp unit → `/barcodes` (tab All). |
| Business Rule | - Ngày tính theo **ngày tạo đơn** (bắt đầu đơn).<br>- Tab, partner, khoảng ngày lưu trên URL. Bấm **Xoá** trong lịch → quay về mặc định 14 ngày.<br>- Ô có giá trị 0 hiển thị mờ.<br>- ⚠️ Link sang `/barcodes` chỉ mở được khi vendor đang mở luồng sản xuất sub-barcode; nếu không sẽ bị chuyển về `/orders`.<br>- ⚠️ Khoảng ngày tối đa không giới hạn trên FE — cần backend confirm. |

#### Các cột chỉ số
| Cột | Cấp | Click mở |
|---|---|---|
| **Total order** | Đơn | Orders |
| **Total sub item order** | Unit | Sub-barcode (tất cả) |
| **New** | Unit | unit còn hiệu lực |
| **Pre-production** | Unit | pre_production |
| **Prepare-file** | Unit | prepare_file |
| **Cut** | Unit | đã qua bước Cut |
| **Printed** / **Not printed** | Unit | đã qua Print / chưa in |
| **QC** / **QC error** | Unit | đã qua QC / lỗi QC |
| **Broken** | Unit | broken |
| **Packaged** / **Not Packaged** | Unit | đã qua Package / chưa đóng gói |
| **Assizes** | Đơn | đơn đã assize |
| **Labeled** / **Not Labeled** | Unit | đã có / chưa có label |
| **Shipped** / **Not shipped** | Đơn | đã / chưa ship |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Khoảng ngày** | Định dạng YYYY-MM-DD; chọn 2 ngày, tự sắp ngày nhỏ trước. | — | — |
| **Partner** | Mã partner ≤ 64 ký tự (chọn từ danh sách). | — | — |
