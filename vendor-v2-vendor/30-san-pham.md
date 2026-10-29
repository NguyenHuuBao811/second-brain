# Sản phẩm (Products)

Route: `/products` — Menu **Catalog › Products**, hiển thị khi user có permission `products.read` (owner, manager, shipping, viewer). Role **production** không có quyền này.
Quyền sửa: `products.write` — chỉ **owner**. Không cần bật Sub-barcode để vào trang này.

### Xem danh sách sản phẩm

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem catalog sản phẩm của vendor (đồng bộ từ FF). |
| Actor | owner, manager, shipping, viewer |
| Trigger | Menu **Products**. |
| Main Flow | 1. Header "Products — Catalog synced from FF".<br>2. Bảng: ảnh mockup, **Code**, **Name**, **Material**, **Status**, **Fastway**, **Created**, menu thao tác.<br>3. Mặc định 100 dòng/trang (20/50/100/200); có checkbox chọn dòng; tổng "N products". |
| Alternative Flow | A1. Chưa có sản phẩm → "No products yet — Products will appear here once synced from FF".<br>A2. Lọc không ra kết quả → "No products match your filters".<br>A3. **Refresh** → tải lại danh sách.<br>A4. Click dòng → mở drawer chi tiết. |
| Business Rule | **Bộ lọc:** ô "Search by code or name…" (debounce 300ms), **Status**: All statuses / Active / Inactive.<br>**Fastway:** Synced / Pending (icon xoay) / Failed (click để xem lỗi) / Chưa sync.<br>Khi có sản phẩm **Pending**, danh sách tự refresh mỗi 5 giây. |

### Đồng bộ sang Fastway (Sync to FW)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Đẩy (enqueue) sản phẩm sang Fastway. |
| Actor | Mọi role vào được trang (nút ở header & menu dòng không kiểm tra `products.write`); nút trong drawer chỉ owner (`products.write`). |
| Trigger | Nút **Sync to FW** (header, theo các dòng đã chọn) / menu dòng **Sync to FW** / **Retry** (dòng Failed) / nút trong drawer / **Retry sync** trong popup lỗi. |
| Main Flow | 1. Click nút.<br>2. Hệ thống enqueue sản phẩm. |
| Post-conditions | Có sản phẩm được enqueue: "Đã enqueue N sản phẩm". Không: "Sản phẩm đã được bỏ qua (skipped)" (1 sản phẩm) hoặc "Không có sản phẩm nào được enqueue" (nút header). |
| Exception Flow | Lỗi → "Sync thất bại". |
| Business Rule | ⚠️ Nút header vẫn bấm được khi chưa chọn dòng nào; backend xử lý danh sách rỗng thế nào chưa xác minh. |

### Xem lỗi sync Fastway

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem nguyên nhân sync Fastway thất bại. |
| Actor | Mọi role vào được trang |
| Trigger | Click badge **Failed** hoặc menu dòng **Xem lỗi**. |
| Main Flow | 1. Popup "Lỗi sync Fastway" + tên sản phẩm + nội dung lỗi.<br>2. **Retry sync** để sync lại. |
| Business Rule | Thiếu trường → "Sản phẩm chưa đủ thông tin để sync Fastway:" + list (Material (chất liệu), Ảnh mockup, Danh sách variants (đang trống); Variant X thiếu Shape type / Length (cm) / Width (cm) / Height (cm) / Weight (g) / Cost). Nếu thiếu ở variant: "Kích thước / cân nặng variant do FF quản lý — cập nhật trên FF…".<br>Lỗi mạng khi tạo → "Tạo product trên Fastway thất bại giữa chừng" (kiểm tra FW dashboard trước khi retry).<br>Mockup lỗi → "Không tải được ảnh mockup" (jpeg/jpg/png ≤ 5MB).<br>Fastway 4xx → "Fastway từ chối yêu cầu"; trùng SKU → cần admin xử lý tay (SKU `<vendorCode>-<sku>`).<br>Không có lỗi → "Không có thông tin lỗi." |

### Yêu cầu FF đồng bộ lại

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Yêu cầu FF đẩy lại toàn bộ sản phẩm hoặc 1 sản phẩm. |
| Actor | owner (`products.write`) |
| Trigger | Nút **Sync from FF** (header: toàn bộ) / menu dòng hoặc drawer **Sync from FF** (1 sản phẩm). |
| Main Flow | Toàn bộ: 1. Popup "Sync sản phẩm từ FF — FF sẽ đẩy lại toàn bộ sản phẩm của bạn. Dữ liệu cập nhật sau ít phút."<br>2. Click **Sync**.<br>1 sản phẩm: gửi yêu cầu ngay, không confirm. |
| Post-conditions | Toàn bộ: "Đã yêu cầu sync — sản phẩm sẽ cập nhật sau ít phút".<br>1 sản phẩm: "Đã yêu cầu FF đồng bộ lại — dữ liệu cập nhật sau khoảng 1 phút". |
| Alternative Flow | 1 sản phẩm chưa gắn với xưởng trên FF → cảnh báo "FF không gắn sản phẩm này với xưởng — kiểm tra liên kết xưởng ↔ sản phẩm trên FF". |
| Exception Flow | Toàn bộ: "Yêu cầu sync thất bại". 1 sản phẩm: "Yêu cầu đồng bộ từ FF thất bại". |

### Xem chi tiết sản phẩm (drawer)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Xem thông tin, variants và hướng dẫn sản xuất của 1 sản phẩm. |
| Actor | owner, manager, shipping, viewer |
| Trigger | Click 1 dòng sản phẩm (link có thể mở thẳng qua query `?product=`). |
| Main Flow | 1. Header: mockup, tên, code; **Material**, **Status**, **Created**, **Updated**.<br>2. Owner thấy thêm nút **Sync to FW**, **Sync from FF**.<br>3. Tab **Variants (N)**: tìm "Tìm theo SKU, Supplier SKU hoặc tên…"; bảng **SKU**, **Supplier SKU**, **Name**, **Shape**, **L (cm)**, **W (cm)**, **H (cm)**, **Weight (g)**; phân trang 20/50/100/200.<br>4. Tab **Hướng dẫn sản xuất**. |
| Alternative Flow | Chưa có variant → "Chưa có variant nào"; tìm không ra → "Không có variant nào khớp". |
| Exception Flow | Sản phẩm không còn → "Sản phẩm không còn tồn tại", đóng drawer. |
| Business Rule | Kích thước/cân nặng variant chỉ xem, không sửa trên UI (do FF quản lý). Không có trường giá trên UI. |

### Sửa Material sản phẩm

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Sửa chất liệu (Material) inline trong drawer. |
| Actor | owner (`products.write`); role khác chỉ xem. |
| Trigger | Click giá trị **Material** (icon bút). |
| Main Flow | 1. Nhập giá trị.<br>2. Enter / nút ✓ để lưu; Esc / nút ✕ để hủy. |
| Post-conditions | "Đã cập nhật material". Nếu sản phẩm đã từng sync và chuyển Pending → "Đã enqueue sync Fastway". |
| Alternative Flow | Để trống → lưu thành rỗng (xóa material). |
| Exception Flow | "Lưu thất bại". |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Material** | Trim; rỗng = xóa; nếu có: 1–128 ký tự | Viền đỏ, nút Save disable (không có message) | — |

### Sửa Shape type của variant

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Sửa **Shape** của 1 variant inline. |
| Actor | owner (`products.write`) |
| Trigger | Icon bút cuối dòng variant. |
| Main Flow | 1. Ô **Shape** chuyển sang input.<br>2. Enter / ✓ để lưu; Esc / ✕ để hủy. |
| Post-conditions | "Đã cập nhật variant". Nếu sản phẩm đã sync (không phải Chưa sync/Pending) → "Đã enqueue sync Fastway". |
| Alternative Flow | A1. Không đổi giá trị → đóng, không gọi API.<br>A2. Đang sửa dòng khác có thay đổi chưa lưu → confirm "Bỏ thay đổi chưa lưu?". |
| Exception Flow | "Lưu thất bại". |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Shape** | Rỗng = xóa; nếu có: 1–64 ký tự | Viền đỏ, nút Save disable | — |

### Hướng dẫn sản xuất theo công đoạn

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Soạn hướng dẫn (rich text + ảnh) cho từng công đoạn của sản phẩm; hiển thị cho công nhân khi quét. |
| Actor | owner (sửa); role khác chỉ xem ("Bạn không có quyền sửa hướng dẫn sản xuất"). |
| Trigger | Tab **Hướng dẫn sản xuất** trong drawer. |
| Main Flow | 1. **Chọn công đoạn** (Print, Cut, QC, Package, Label).<br>2. Nhập hướng dẫn: Đậm, Nghiêng, Gạch chân, Tiêu đề lớn/nhỏ, danh sách chấm/số, Chèn link (http/https), Tô vàng, chữ đỏ/cam/xanh lá/xanh dương, Xoá định dạng; bộ đếm ký tự.<br>3. **Ảnh**: kéo-thả, dán (Ctrl+V) hoặc bấm chọn.<br>4. **Lưu hướng dẫn**. |
| Post-conditions | "Đã lưu hướng dẫn sản xuất". |
| Exception Flow | E1. Tải lỗi → "Không tải được hướng dẫn sản xuất. Vui lòng thử lại."<br>E2. Lưu lỗi → "Lưu hướng dẫn thất bại".<br>E3. Upload ảnh lỗi → "Upload ảnh thất bại, vui lòng thử lại". |
| Business Rule | ⚠️ Màn hình này nằm ở chunk tải riêng, không có trong bundle — mô tả dựa trên i18n và schema. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Hướng dẫn** | ≤ 10.000 ký tự (text thuần) | Hướng dẫn vượt quá 10.000 ký tự | Guidance exceeds 10,000 characters |
| **Ảnh** | ≤ 5 ảnh / công đoạn; URL ≤ 512 ký tự | ⚠️ chưa xác minh message | — |

### Export sản phẩm

| Mục | Nội dung |
|---|---|
| Actor | Mọi role vào được trang |
| Main Flow | Menu **Export** → **Export by filter (N)** (theo search/status) hoặc **Export selected (N)** (disable khi chưa chọn) → tải file `.xlsx`. |
| Exception Flow | "Export thất bại". |

### Import thông số Fastway

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Upload Excel để cập nhật thông số Fastway (giá, mã…) cho variant. |
| Actor | Mọi role vào được trang (nút không kiểm tra permission — ⚠️ backend có chặn theo `products.write` hay không chưa xác minh). |
| Trigger | Nút **Import**. |
| Main Flow | 1. Popup "Import sản phẩm — Fastway fields": kéo-thả hoặc **Chọn file .xlsx**.<br>2. Preview: "N cập nhật", "N lỗi"; cột **Sẽ cập nhật** (bảng Field / Trước / Sau theo SKU) và **Lỗi** (Row X [SKU] + message).<br>3. **Apply (N)**. |
| Post-conditions | "Đã apply X dòng, enqueue Y sản phẩm để sync", đóng popup. |
| Alternative Flow | **Tải lại file** → về bước chọn file; **Đóng** → hủy. |
| Exception Flow | E1. File > 5 MB → "File quá lớn — tối đa 5 MB".<br>E2. Không parse được → "Không thể phân tích file — hãy kiểm tra lại định dạng .xlsx".<br>E3. Preview có lỗi → **Apply** disable.<br>E4. Apply lỗi → "Apply thất bại — vui lòng thử lại". |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **File** * | Định dạng .xlsx | Không thể phân tích file — hãy kiểm tra lại định dạng .xlsx | — |
| **File** * | ≤ 5 MB | File quá lớn — tối đa 5 MB | — |
