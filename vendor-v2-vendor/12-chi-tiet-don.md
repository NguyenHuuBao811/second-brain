# Chi tiết đơn & chi tiết item

Routes: `/orders/:id`, `/orders/:id/items/:itemId` — Role: mọi user đã đăng nhập (`orders.read`).
Danh sách đơn: [11-don-hang.md](11-don-hang.md). Phiên bản admin: [../vendor-v2-admin/03-don-hang.md](../vendor-v2-admin/03-don-hang.md).

**Nút trên header chi tiết đơn**

| Nút | Permission | Điều kiện hiển thị thêm |
|---|---|---|
| **Gán Priority / Gỡ Priority** | `orders.set_priority` | Chỉ user vendor (ẩn với staff PW/admin); status = **New** |
| **Print barcode** | `orders.print_barcode` | Luôn |
| **View label** | `orders.print_label` | Đơn đã có label |
| **Back error artwork** | `orders.back_error` | Xem UC "Back error artwork" |
| **Send to Ship** | `orders.ship` | Đơn đủ điều kiện Send to Ship (cùng rule bulk ở [11-don-hang.md](11-don-hang.md#send-to-ship-hàng-loạt)) |
| **Sửa** (địa chỉ) | `orders.update_address` | Status ∉ {Shipped, Canceled, Shipping Refunded, On Hold} |
| **Thêm/Sửa note sản xuất** | — | Chỉ user vendor (ẩn với staff PW/admin) |

> Assize, Buy label, Re-weigh **không** có trên màn chi tiết đơn — thực hiện tại các trạm sản xuất ([20-tram-assize.md](20-tram-assize.md), [21-tram-label.md](21-tram-label.md)).

### Xem chi tiết đơn

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem đầy đủ thông tin 1 đơn của vendor. |
| Actor | owner, manager, production, shipping, viewer, staff PW |
| Trigger | Click 1 đơn ở danh sách, hoặc mở link `/orders/:id`. |
| Main Flow | 1. Header: nút quay lại **Orders**, PW Order ID (copy), mã Partner, ngày nhận, Status, Type, badge **Đơn ghép**, tag **Priority**, badge **Re-weighing** (đang chờ mua lại label sau cân lại).<br>2. Thanh tiến độ: **Sản xuất → Assize → Label → Shipping** (đơn Sample/Bulk chỉ **Sản xuất → Shipping**); mỗi bước Chờ xử lý / Đang xử lý / Hoàn thành.<br>3. Cột trái: **Items (N)** — mỗi item 1 card.<br>4. Cột phải: **Hoạt động** (audit + lịch sử label, **Xem thêm**), **Chi tiết đơn** (Name, Tracking, Total ship fee, Created), **Giao hàng** (địa chỉ + Dịch vụ vận chuyển + Hãng giao hàng), **Kích thước (thực tế)** (Length/Width/Height cm, Weight g), **Vận chuyển** (routing events). |
| Alternative Flow | A1. Đơn TikTok có label từ FF → dòng giải thích + link **Xem label TikTok**.<br>A2. Đơn **On Hold** → banner "Đơn đang On Hold bởi FF – Vendor không thể thao tác đơn này cho tới khi FF un-hold. Hold lúc …" + **Lý do**.<br>A3. Click mũi tên trên item có barcode → Chi tiết item. |
| Business Rule | - Thanh Sản xuất "Hoàn thành" khi đơn không có item quản lý theo unit, hoặc đã xong toàn bộ unit.<br>- Card item hiển thị: mockup (phóng to được), tên SP (chưa sync → "(Sản phẩm chưa sync)"), loại SP, trạng thái sản xuất / "Not started" / Artwork Error, Variant, SKU, BARCODE, Supplier, Qty, Ship fee, Cost (= đơn giá × qty), **Ghi chú của partner**, ghi chú phụ kiện của seller, **Note sản xuất**, khối **Bàn in** (job & file AD).<br>- Item bị cancel → gạch ngang, mờ, nhãn "Canceled" + lý do.<br>- Item lỗi artwork → khung đỏ "Lỗi artwork" + loại lỗi, thời gian, lý do, ảnh evidence (xem lớn). |

### Xem artwork & in tem sub-barcode của item

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem file thiết kế của item; in tem sub-barcode. |
| Actor | Mọi user xem được đơn |
| Trigger | Nút **Xem artwork (N)** / **In tem sub-barcode** trên card item. |
| Main Flow | **Xem artwork**: popup "Artwork – {product}", hiển thị N artwork, có **Tải về** / **Mở ảnh gốc**, **Đóng**.<br>**In tem sub-barcode**: mở tab mới hiển thị PDF tem sub-barcode của item. |
| Exception Flow | In tem lỗi → "Không mở được tem sub-barcode" / "Could not open the sub-barcode sheet". Tải artwork lỗi → "Tải artwork thất bại" / "Artwork download failed". |
| Business Rule | - **Xem artwork** disable khi item không có design.<br>- **In tem sub-barcode** chỉ hiện khi item có barcode.<br>- ⚠️ Nút **In tem sub-barcode** không kiểm tra permission ở FE. |

### Thêm / sửa note sản xuất

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Ghi chú cho bộ phận sản xuất trên từng item. |
| Actor | User vendor (ẩn với staff PW/admin) |
| Trigger | **Thêm note sản xuất** (chưa có note) hoặc icon **Sửa note sản xuất**. |
| Post-conditions | Note được lưu và hiển thị trên card item. |
| Main Flow | 1. Hiện ô nhập (placeholder "Ghi chú cho bộ phận sản xuất…").<br>2. Click **Lưu** → lưu; hoặc **Huỷ** / phím Esc → thoát. |
| Exception Flow | Lỗi → "Không lưu được note sản xuất" / "Could not save the production note". |
| Business Rule | - Nội dung được trim; để trống → xoá note.<br>- ⚠️ Không kiểm tra permission/status đơn ở FE (kể cả viewer, đơn Shipped/Canceled) — cần BE confirm. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Note sản xuất** | Optional; ≤ 1.000 ký tự (chặn nhập) | — | — |

### Gán / gỡ Priority (1 đơn)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Bật/tắt ưu tiên cho đơn đang xem. |
| Actor | User vendor có `orders.set_priority` (owner, manager, production, shipping) |
| Trigger | Nút **Gán Priority** / **Gỡ Priority** (EN: **Mark Priority** / **Unmark Priority**). |
| Pre-conditions | Status = **New**. |
| Post-conditions | Toast "Đã cập nhật Priority" / "Priority updated"; tag **Priority** hiện/ẩn. |
| Exception Flow | `priority_not_new` → "Chỉ gán/gỡ Priority khi đơn ở trạng thái New" / "Priority can only be changed while the order is New"; khác → "Có lỗi xảy ra" / "Internal error". |

### In barcode đơn

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | In barcode PW Order ID của đơn. |
| Actor | User có `orders.print_barcode` (owner, manager, production, shipping) |
| Trigger | Nút **Print barcode**. |
| Main Flow | 1. Popup **Print barcode** hiển thị barcode + mã PW Order ID.<br>2. **Print** → hộp thoại in của trình duyệt; **Close** → đóng. |

### Send to Ship (1 đơn)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Chuyển đơn sang **Shipped**. |
| Actor | User có `orders.ship` (owner, manager, production, shipping, staff PW) |
| Trigger | Nút **Send to Ship**. |
| Pre-conditions | Đơn đủ điều kiện (New; Sample/Bulk ở New/In production; In production/Assized/Labeled đã có label). |
| Post-conditions | Toast "Đã chuyển đơn sang Shipped" / "Order marked as Shipped"; reload đơn & danh sách. |
| Main Flow | Click nút → gửi ngay, không có popup xác nhận. Nút disable trong lúc gửi. |
| Exception Flow | Lỗi theo mã (bảng lý do ở [11-don-hang.md](11-don-hang.md#send-to-ship-hàng-loạt)); mặc định "Có lỗi xảy ra" / "Internal error". |
| Business Rule | ⚠️ Không có bước xác nhận — bấm nhầm là ship ngay. |

### Back error artwork

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Báo lỗi artwork cho từng item về FF (FF nhận webhook và thông báo seller). |
| Actor | User có `orders.back_error` (owner, manager, production) |
| Trigger | Nút **Back error artwork** (đỏ). |
| Pre-conditions | - Status **New** hoặc **In production**, hoặc **Artwork Error** với loại lỗi do FF (`artwork_ff`).<br>- Đơn không **On Hold**.<br>- Có ≥ 1 item đủ điều kiện: liên kết FF, chưa bị báo lỗi, trạng thái sản xuất là chưa bắt đầu / New / Pre-production / Exported-barcode. |
| Post-conditions | Toast "Đã báo về FF"; đóng popup; reload đơn & danh sách. |
| Main Flow | 1. Popup **Back error artwork** – "Báo lỗi artwork cho từng item — ảnh sẽ được upload khi nhấn Confirm."<br>2. Click **Add item** → thêm 1 dòng, chọn **Item** (dropdown "Chọn item lỗi": tên · SKU · barcode).<br>3. Với mỗi item: chọn **Error type**, nhập **Reason**, thêm **Images** (kéo thả / chọn / dán ảnh vào ô Reason).<br>4. Click **Confirm** → "Đang upload…" (upload ảnh) → "Đang gửi…" (gửi báo lỗi). |
| Alternative Flow | A1. Icon X → xoá dòng item.<br>A2. **Hủy** → đóng popup, xoá dữ liệu.<br>A3. Chưa có dòng → "Chưa có item nào. Nhấn "+ Add item" để bắt đầu."<br>A4. Đã thêm hết item → **Add item** disable, "Tất cả items đã được thêm."; không có item hợp lệ → "Order has no FF-linked items." |
| Exception Flow | E1. Upload ảnh lỗi → "Upload ảnh thất bại: {lỗi}. Vui lòng thử lại." (không gửi báo lỗi).<br>E2. Gửi lỗi → "Báo lỗi thất bại". |
| Business Rule | - Mỗi item chỉ chọn 1 lần.<br>- **Confirm** chỉ bật khi có ≥ 1 dòng và mọi dòng đủ: Item, Error type (nếu "Lỗi khác" thì phải mô tả), Reason, ≥ 1 ảnh.<br>- Trong lúc gửi: mọi nút disable, không đóng được popup.<br>- **Error type**: Bong/tách rời, Nét quá mảnh, Nền tách chưa sạch, Sai template, File không đạt chuẩn, File không khớp, File chưa lật, Khách yêu cầu trả artwork, Thiếu lỗ treo/dây, Sai định dạng file, Thiếu vị trí sticker, Lỗi khác.<br>- Text popup (trừ tên loại lỗi) chỉ tiếng Việt. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Item** * | Bắt buộc; không trùng item dòng khác | (Nút **Confirm** disable) | — |
| **Error type** * | Bắt buộc, chọn từ danh sách | (Nút **Confirm** disable) | — |
| **Mô tả loại lỗi** | Bắt buộc khi Error type = Lỗi khác; trim ≥ 1 ký tự; ≤ 120 ký tự (chặn nhập) | (Nút **Confirm** disable) | — |
| **Reason** * | Trim ≥ 1 ký tự | (Nút **Confirm** disable) | — |
| **Images** * | 1–5 ảnh/item; vượt 5 → bỏ qua file thừa | (Nút **Confirm** disable khi 0 ảnh) | — |
| **Images** | Chỉ file ảnh | {tên file}: chỉ chấp nhận ảnh | — |
| **Images** | ≤ 10 MB/ảnh | {tên file}: vượt quá 10 MB | — |

### Sửa địa chỉ giao hàng

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Sửa địa chỉ người nhận của đơn. Form, luồng xác nhận lý do và validation giống bản admin — xem [Sửa địa chỉ giao hàng (admin)](../vendor-v2-admin/03-don-hang.md#sửa-địa-chỉ-giao-hàng-admin). |
| Actor | User có `orders.update_address` (mặc định chỉ staff PW; vendor cần owner cấp quyền) |
| Trigger | Nút **Sửa** ở card **Giao hàng**. |
| Pre-conditions | Status ∉ {Shipped, Canceled, Shipping Refunded, On Hold}. |
| Business Rule | - Khác admin: dùng permission `orders.update_address` (thay vì `admin.orders.update_address`).<br>- Nút **Xác nhận & lưu** chỉ bật khi **Lý do chỉnh sửa** có nội dung (trim) → lý do là **bắt buộc**; ≤ 500 ký tự (chặn nhập).<br>- ⚠️ Vendor role mặc định không có quyền này → nút **Sửa** ẩn với owner/manager/... trừ khi được override. |

### Xem chi tiết item (sub-barcode units)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem các unit (sub-barcode) của 1 item và tiến độ sản xuất từng unit. |
| Actor | Mọi user xem được đơn |
| Trigger | Mũi tên **Xem chi tiết đơn vị** trên card item (chỉ item có barcode). |
| Main Flow | 1. Sidebar trái: **Quay lại** (về chi tiết đơn), PW Order ID (copy), tên đơn, **Sản phẩm trong đơn (N)** — click để chuyển item.<br>2. Header: tên SP, **SKU**, **Loại sản phẩm**, barcode, trạng thái sản xuất (hoặc Artwork Error), nút **Xem artwork**.<br>3. Danh sách **Đơn vị sản phẩm (N)** (EN: "Sub Barcode Item"): mỗi unit hiển thị mã sub-barcode (copy), trạng thái, tiến độ theo workflow + các mốc Assize/Label/Shipping.<br>4. 10 unit/trang, nút **Trước** / **Sau** + "x-y / tổng". |
| Alternative Flow | Item không có unit → "Sản phẩm này không dùng sub-barcode" / "This item does not use sub-barcodes". |
| Business Rule | - Unit bị huỷ → mờ, gạch ngang.<br>- Đổi item → quay về trang 1.<br>- Chỉ xem, không có thao tác chỉnh sửa. |
