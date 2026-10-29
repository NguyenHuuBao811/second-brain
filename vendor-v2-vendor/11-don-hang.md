# Đơn hàng (Orders – danh sách)

Route: `/orders` — Role: mọi user đã đăng nhập (`orders.read`). Nút/hành động ẩn hiện theo permission (bảng ở [00-README.md](00-README.md)).
Chi tiết đơn / item: xem [12-chi-tiet-don.md](12-chi-tiet-don.md). Phía admin (cross-vendor): [../vendor-v2-admin/03-don-hang.md](../vendor-v2-admin/03-don-hang.md).

**Hiển thị nút theo permission (màn danh sách)**

| Nút / hành động | Điều kiện hiển thị |
|---|---|
| **Refresh** | Mọi user |
| **Export** | User vendor (ẩn với staff PW / admin / super_admin) |
| **New sync** | Luôn hiển thị nhưng **luôn disable** ⚠️ (chưa có chức năng) |
| **Import tracking** | `orders.bulk_actions` |
| Thanh bulk action (khi tick dòng) | `orders.bulk_actions` |
| **Gán Priority / Gỡ Priority** (bulk) | `orders.bulk_actions` + `orders.set_priority` |
| Cột **Label** → **View** | `orders.print_label` (không có quyền → hiện "—") |

### Xem danh sách đơn của vendor

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem hàng đợi đơn sản xuất (**Orders** – "Production queue") của vendor, lọc, phân trang. |
| Actor | owner, manager, production, shipping, viewer (và staff PW — xem dữ liệu qua API staff) |
| Trigger | Menu **Đơn hàng** / **Orders**; hoặc sau đăng nhập (role vendor). |
| Pre-conditions | Đã đăng nhập. |
| Main Flow | 1. Mặc định lọc **30 ngày gần nhất** theo ngày nhận đơn, **100 dòng/trang**.<br>2. Bảng cột: **PW Order ID** (copy), **Type** (+ badge **Đơn ghép/Merged** nếu đơn ghép), **Products**, **Artwork**, **Ship fee**, **Tracking**, **Label**, **Status**, **Received**, **Qty**.<br>3. Góc phải thanh lọc hiển thị tổng "**N orders**".<br>4. Click dòng → Chi tiết đơn `/orders/:id`. |
| Alternative Flow | A1. Đơn ≥ 2 item → mở rộng dòng xem từng item (kèm trạng thái sản xuất từng item).<br>A2. Click **Artwork** → popup xem thiết kế các item.<br>A3. Cột **Tracking**: có lỗi mua label → badge **Lỗi label**; click → popup **Lỗi mua label Fastway** hiển thị lý do (không có → "Không có thông tin lỗi."). Có tracking → link sang trang tracking (nếu có URL) + copy.<br>A4. Đơn Priority → tag **Priority** màu cam ở cột Tracking.<br>A5. Cột **Label** có label → **View** → popup Label (xem UC "Xem / in label").<br>A6. **Refresh** → tải lại, toast "Refreshing…".<br>A7. Không có kết quả → "No orders match your filters" + nút reset filter (xoá filter & khoảng ngày → quay về mặc định 30 ngày). |
| Business Rule | **Bộ lọc** (lưu trên URL, đổi filter → về trang 1):<br>- **Search**: theo mã đơn, nhiều mã cách nhau bởi dấu phẩy, Tab hoặc Enter; tự loại trùng (không phân biệt hoa thường); debounce 300 ms.<br>- **Status**: Tất cả trạng thái / New, In production, Assized, Labeled, Shipped, Artwork Error, On Hold, Canceled, Shipping Refunded.<br>- **Type**: Tất cả loại đơn / Basic, TikTok, TikTok by seller, Sample, Bulk.<br>- **Tình trạng label**: Tất cả label / Đã có label / Chưa có label / Label lỗi.<br>- **Khoảng ngày** (ngày nhận đơn).<br>- Page size: 20 / 50 / 100 / 200.<br>- Search không hợp lệ → không gọi API, ô search viền đỏ + message, menu **Export by filter** disable.<br>- Products: 1 item → tên SP · variant + SKU; nhiều item → "N items · X canceled" + danh sách loại SP.<br>- Đơn có **toàn bộ** item bị cancel → cả dòng gạch ngang. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Search** | ≤ 50 mã (sau khi loại trùng) | Tối đa 50 mã một lần tìm. | At most 50 codes per search. |
| **Search** | ≤ 2.000 ký tự | Chuỗi tìm kiếm quá dài, tối đa 2000 ký tự. | Search text is too long — at most 2000 characters. |
| **Search** | Có ít nhất 1 mã (không chỉ toàn dấu phân cách) | Không có mã đơn nào để tìm. | No order code to search for. |

### Export đơn hàng

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xuất file Excel đơn (định dạng Fastway) theo bộ lọc hoặc dòng đã chọn. |
| Actor | owner, manager, production, shipping, viewer (không hiển thị với staff PW) |
| Trigger | Nút **Export** → chọn menu. |
| Main Flow | **Export by filter (N)**: xuất toàn bộ đơn khớp filter hiện tại (N = tổng đơn).<br>**Export selected (N)**: xuất các dòng đã tick.<br>Trình duyệt tải file `.xlsx` (tên theo BE, mặc định `fw-orders.xlsx`). |
| Exception Flow | Lỗi → toast "Export thất bại" (chỉ tiếng Việt). |
| Business Rule | - **Export by filter** disable khi ô search không hợp lệ.<br>- **Export selected** disable khi chưa tick dòng nào.<br>- Nút **Export** disable + nhấp nháy trong lúc đang xuất.<br>- Khác admin: vendor **không** cần chọn vendor. |

### Send to Ship hàng loạt

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Chuyển nhiều đơn sang **Shipped** cùng lúc. |
| Actor | User có `orders.bulk_actions` (owner, manager, production, shipping) |
| Trigger | Tick ≥ 1 dòng → nút **Send to Ship (N)** trên thanh bulk. |
| Pre-conditions | Có ≥ 1 đơn đủ điều kiện trong các dòng đã tick (N = số đơn đủ điều kiện; N = 0 → nút disable). |
| Post-conditions | Đơn đủ điều kiện → **Shipped**; bỏ chọn tất cả; danh sách reload. |
| Main Flow | 1. Tick các đơn.<br>2. Click **Send to Ship (N)** → chỉ gửi các đơn đủ điều kiện.<br>3. Toast "Đã chuyển {count} đơn sang Shipped" / "{count} orders marked as Shipped". |
| Alternative Flow | Có đơn bị BE bỏ qua → toast cảnh báo "Đã chuyển {shipped} đơn sang Shipped. Bỏ qua: {reasons}" / "{shipped} orders marked as Shipped. Skipped: {reasons}" (lý do gom nhóm, vd "Đơn đã hủy ×2"). |
| Exception Flow | Lỗi API → toast lỗi theo mã (bảng lý do bên dưới), mặc định "Có lỗi xảy ra" / "Internal error". |
| Business Rule | **Đơn đủ điều kiện Send to Ship** (FE):<br>- Status **New** → luôn đủ.<br>- Đơn **Sample/Bulk** ở New / In production → đủ.<br>- Status **In production / Assized / Labeled** → cần đã có label (label vendor hoặc label TikTok).<br>- Status khác (Shipped, Artwork Error, On Hold, Canceled, Shipping Refunded) → không đủ.<br>⚠️ Việc gửi đơn New/chưa có label sang Shipped được FE cho phép; BE có thể từ chối (`order_not_labeled`). |

**Lý do bỏ qua / lỗi (VI / EN)**

| Mã | VI | EN |
|---|---|---|
| order_canceled | Đơn đã hủy | Order is canceled |
| order_shipping_refunded | Đơn đã hoàn phí vận chuyển | Order shipping fee was refunded |
| order_on_hold | Đơn đang bị giữ (OnHold) | Order is on hold |
| order_in_error | Đơn đang ở trạng thái lỗi | Order is in an error state |
| order_already_shipped | Đơn đã ở trạng thái Shipped | Order is already Shipped |
| order_not_labeled | Đơn chưa có label — hãy mua label trước khi Send to Ship | Order has no label yet — buy a label before Send to Ship |
| not_found | Không tìm thấy đơn | Order not found |

### Gán / gỡ Priority hàng loạt

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Đánh dấu hoặc bỏ đánh dấu ưu tiên cho nhiều đơn. |
| Actor | User có `orders.bulk_actions` + `orders.set_priority` (owner, manager, production, shipping) |
| Trigger | Tick dòng → **Gán Priority (N)** / **Gỡ Priority (N)** (EN: **Mark Priority (N)** / **Unmark Priority (N)**). |
| Pre-conditions | N = số đơn đã tick đang ở **New** và chưa ở trạng thái đích (Gán: đơn chưa Priority; Gỡ: đơn đang Priority). N = 0 → nút disable. |
| Post-conditions | Đơn được cập nhật cờ Priority; bỏ chọn; reload danh sách & hàng đợi sub-barcode. |
| Main Flow | 1. Tick đơn → click nút.<br>2. Toast "Đã cập nhật {updated} đơn, bỏ qua {skipped} đơn (không ở trạng thái New hoặc đã đúng)" / "Updated {updated} orders, skipped {skipped} (not New or already set)". |
| Alternative Flow | skipped > 0 → toast dạng cảnh báo (vàng) thay vì thành công. |
| Exception Flow | Lỗi `priority_not_new` → "Chỉ gán/gỡ Priority khi đơn ở trạng thái New" / "Priority can only be changed while the order is New"; lỗi khác → "Có lỗi xảy ra" / "Internal error". |

### In barcode PDF hàng loạt

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Tải 1 file PDF chứa barcode của các đơn đã chọn. |
| Actor | User có `orders.bulk_actions` |
| Trigger | Tick dòng → **Print barcode PDF**. |
| Post-conditions | Tải file `barcodes-YYYY-MM-DD.pdf`; bỏ chọn. |
| Main Flow | 1. Tick đơn → click nút.<br>2. Toast "PDF downloaded". |
| Exception Flow | Lỗi → toast "Failed to download PDF". |
| Business Rule | - Không lọc theo status, mọi đơn đã tick đều gửi lên.<br>- ⚠️ Nút nằm trong thanh bulk nên chỉ cần `orders.bulk_actions`, không kiểm tra `orders.print_barcode`. |

### Import tracking (Sample/Bulk)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Cập nhật tracking hàng loạt cho đơn Sample/Bulk bằng file Excel. |
| Actor | User có `orders.bulk_actions` |
| Trigger | Nút **Import tracking**. |
| Post-conditions | Tracking của các dòng hợp lệ được cập nhật. |
| Main Flow | 1. Mở popup **Import tracking** – "Tải file .xlsx (cột 1: mã đơn, cột 2: tracking). Chỉ cập nhật tracking cho đơn Sample/Bulk."<br>2. (Tuỳ chọn) **Tải file mẫu (.xlsx)** → tải `import-tracking-template.xlsx`.<br>3. Kéo & thả hoặc **Chọn file .xlsx** → hệ thống phân tích (preview) — "Đang phân tích file…".<br>4. Hiển thị tên file, badge "N sẵn sàng", "N lỗi"; 2 cột: **Sẽ cập nhật (N)** (mã đơn + tracking) và **Lỗi (N)** ("Row X · mã đơn" + lý do).<br>5. Click **Cập nhật (N)** → toast "Đã cập nhật tracking cho {updated} đơn ({errors} lỗi)", đóng popup. |
| Alternative Flow | A1. **Tải lại file** → quay lại bước chọn file.<br>A2. **Đóng** → đóng popup, xoá dữ liệu preview. |
| Exception Flow | E1. Phân tích thất bại → "Không thể phân tích file — kiểm tra lại .xlsx (cột 1 mã đơn, cột 2 tracking)".<br>E2. Cập nhật thất bại → "Apply thất bại — vui lòng thử lại". |
| Business Rule | - Nút **Cập nhật** chỉ bật khi có ≥ 1 dòng "sẵn sàng"; khi đang cập nhật → "Đang cập nhật…", các nút khác disable.<br>- Khi apply, FE gửi lại **toàn bộ file**, BE tự lọc dòng hợp lệ.<br>- Không có dòng hợp lệ → "Không có dòng hợp lệ"; không có lỗi → "Không có lỗi".<br>- ⚠️ Lý do lỗi từng dòng (sai mã, không phải Sample/Bulk, trạng thái…) do BE trả, hiển thị nguyên văn.<br>- Toàn bộ text popup chỉ có tiếng Việt (không i18n). |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **File** | Chỉ nhận `.xlsx` (bộ chọn file) ⚠️ kéo-thả không kiểm tra đuôi ở FE | Không thể phân tích file — kiểm tra lại .xlsx (cột 1 mã đơn, cột 2 tracking) | — (không có bản EN) |
| **File** | ≤ 5 MB | File quá lớn — tối đa 5 MB | — (không có bản EN) |

### Xem / in label (từ danh sách)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem ảnh label vận chuyển, tải về hoặc in. Dùng chung cho danh sách và chi tiết đơn. |
| Actor | User có `orders.print_label` (owner, manager, production, shipping) |
| Trigger | Cột **Label** → **View** (danh sách) hoặc nút **View label** (chi tiết đơn). |
| Pre-conditions | Đơn đã có label. |
| Main Flow | 1. Popup **Label · {PW Order ID}** (copy) + **Tracking**.<br>2. Tải và hiển thị ảnh label.<br>3. **Download** → tải `label-{tracking hoặc PW Order ID}.{đuôi}`.<br>4. **Print** → mở hộp thoại in của trình duyệt (khổ không lề).<br>5. **Close** → đóng. |
| Exception Flow | Không tải được → "Không tải được label" – "Có thể carrier chưa publish label — thử lại sau."; **Download**/**Print** disable. Bấm khi chưa load xong → "Label chưa load xong". |
