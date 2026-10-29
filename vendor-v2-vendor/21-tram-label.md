# Trạm Label

Route: `/production/label` — Menu **Scanning › Label**: role staff thấy theo role; role vendor thấy khi có permission `orders.print_label` (owner, manager, production, shipping). Route không chặn quyền; nút trong trang không check permission ở FE ⚠️ (BE check `orders.buy_label`, `orders.confirm_label`, `orders.reweigh`).

Bố cục: tiêu đề **Label**, ô quét, cột trái = artwork + card trạng thái label + hướng dẫn dán label theo sản phẩm ("Cách dán label — {product}:"), cột phải = panel đơn & unit.

### Quét đơn ở trạm Label

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Tra cứu đơn để xem/mua/in label. |
| Actor | staff, owner, manager, production, shipping |
| Trigger | Quét barcode / sub-barcode hoặc gõ pwOrderId + Enter / **Enter barcode**. |
| Pre-conditions | Đơn ở trạng thái **Assized** hoặc **Labeled**. |
| Post-conditions | Hiển thị card trạng thái label phù hợp (xem Business Rule). |
| Main Flow | 1. Quét mã.<br>2. Hệ thống tra cứu đơn, tải chi tiết (label, sản phẩm chặn sync FW, hướng dẫn dán label).<br>3. Hiển thị card theo trạng thái. |
| Exception Flow | E1. Trạng thái khác → "Order chưa ở bước Label (current: {status})".<br>E2. 404 → "Order không tìm thấy"; lỗi khác → "Lỗi tra cứu". |
| Business Rule | Card hiển thị:<br>- **Chưa có label** (Assized, chưa request label lần nào): "Đơn đã Assize nhưng chưa được request label. Bấm để gửi sang Fastway." + nút **Buy label**.<br>- **Đang chờ label…** (Assized đã request, hoặc Labeled đang chờ relabel): "Polling mỗi 5s — sẽ tự confirm khi label về." / khi relabel: "Label cũ đã bị huỷ. Polling mỗi 5s — tracking mới sẽ tự hiện khi label về."<br>- **Label thất bại (Seq #n)** / **Label timeout (Seq #n)**: lý do lỗi + nút **Re-weigh & retry**.<br>- **Label ready** (Labeled, không chờ relabel): **Tracking**, **Carrier**, link **Preview PDF**, nút **Print label**, **Re-weigh**.<br>- Polling tự động 5s khi đơn Assized hoặc đang pendingRelabel. |

### Mua label (Buy label)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Gửi yêu cầu mua label sang Fastway cho đơn đã Assize. |
| Actor | staff, owner, manager, production (permission `orders.buy_label` ⚠️ BE) |
| Trigger | Click **Buy label** ở card **Chưa có label**. |
| Pre-conditions | Đơn Assized, chưa có label; không phải đơn ghép; không có sản phẩm chặn sync FW. |
| Post-conditions | Toast "Đã request label — chờ Fastway callback"; card chuyển **Đang chờ label…**. |
| Main Flow | 1. Click **Buy label** (spinner khi đang gửi).<br>2. Hệ thống gửi request. |
| Exception Flow | E1. Có sản phẩm chưa sync FW → cảnh báo vàng "Cần sync sản phẩm lên Fastway trước khi mua label" + danh sách sản phẩm (trạng thái) + link "Đi tới trang sản phẩm"; nút disable, tooltip "Sync {products} lên Fastway trước khi mua label".<br>E2. Lỗi API → hiển thị message từ API, hoặc "Buy label thất bại". |
| Business Rule | Đơn ghép (merged): không có nút mua, hiển thị "Đơn ghép — chờ FF đẩy label và tracking xuống, không cần mua label". |

### Tự xác nhận label (Confirm label)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Hệ thống tự xác nhận label khi label về. |
| Actor | Hệ thống (người dùng đang mở trạm) |
| Trigger | Dữ liệu đơn cho thấy Assized, không chờ relabel, đã có tracking number và label URL. |
| Post-conditions | ⚠️ Đơn chuyển **Labeled** (do BE). Refresh chi tiết và sub-barcode của đơn. |
| Main Flow | 1. Polling 5s phát hiện label đã về.<br>2. FE tự gọi confirm label (không cần click). |
| Exception Flow | Lỗi confirm bị bỏ qua (không toast). |
| Business Rule | Label chỉ được confirm khi có người đang mở trạm Label với đơn đó ⚠️ (có thể BE cũng tự confirm — chưa xác minh). |

### In label (Print label)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem, tải và in file label vận chuyển. |
| Actor | staff, owner, manager, production, shipping |
| Trigger | Click **Print label** ở card **Label ready**. |
| Pre-conditions | Đơn Labeled, có label URL (không có → nút disable). |
| Main Flow | 1. Popup **Label · {pwOrderId}** (nút copy), dòng "Tracking: …".<br>2. Hệ thống tải file label, hiển thị ảnh.<br>3. **Print** → mở hộp thoại in của trình duyệt (lề 0).<br>4. **Download** → tải `label-{tracking hoặc pwOrderId}.{ext}`.<br>5. **Close**. |
| Alternative Flow | A1. Link **Preview PDF** ở card mở label URL ở tab mới. |
| Exception Flow | E1. Không tải được file → "Không tải được label" / "Có thể carrier chưa publish label — thử lại sau."; nút Print/Download disable.<br>E2. Bấm khi chưa load xong → "Label chưa load xong". |

### Cân lại (Re-weigh) ở trạm Label

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Nhập lại kích thước/cân nặng, huỷ đơn FW cũ và tạo label mới. |
| Actor | staff, owner, manager, production (permission `orders.reweigh` ⚠️ BE) |
| Trigger | Click **Re-weigh** (card Đang chờ label / Label ready) hoặc **Re-weigh & retry** (card thất bại/timeout). |
| Pre-conditions | Đơn **không phải đơn ghép** (riêng nút Re-weigh & retry vẫn hiện với đơn ghép ⚠️). |
| Post-conditions | Toast "Re-weigh requested — chờ label mới…"; đơn chuyển trạng thái chờ label mới. |
| Main Flow | 1. Popup **Re-weigh {pwOrderId}**, điền sẵn dimension hiện tại.<br>2. Sửa **LENGTH**, **WIDTH**, **HEIGHT** (cm), **WEIGHT** (g).<br>3. Click **Submit** ("Submitting…"). |
| Alternative Flow | A1. **Huỷ** → đóng popup. |
| Exception Flow | E1. Field không hợp lệ → "Dimension phải > 0".<br>E2. `fw_cancel_refused` → "FW từ chối huỷ đơn FW cũ (hàng đã vào kho hoặc label đã mua với hãng) — không cân lại được. Liên hệ support FW."<br>E3. Lỗi khác → "Re-weigh failed". |
| Business Rule | Hint card chờ: "FW chưa trả label? Re-weigh sẽ huỷ đơn Fastway cũ và tạo đơn mới với dimension mới." Hint card lỗi: "Re-weigh để tạo lại label sequence mới — hệ thống sẽ retry Fastway với dimensions cập nhật." |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **LENGTH** (cm) | Số, > 0 | Dimension phải > 0 | Dimension must be > 0 |
| **WIDTH** (cm) | Số, > 0 | Dimension phải > 0 | Dimension must be > 0 |
| **HEIGHT** (cm) | Số, > 0 | Dimension phải > 0 | Dimension must be > 0 |
| **WEIGHT** (g) | Số nguyên, > 0 | Dimension phải > 0 | Dimension must be > 0 |
