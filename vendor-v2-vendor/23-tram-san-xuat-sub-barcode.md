# Trạm sản xuất sub-barcode (Print / Cut / QC / Package)

Route: `/production/step/:baseType` (`baseType` = print, cut, qc/qc_pass, package) — Chỉ vào được khi vendor có trạm sản xuất sub-barcode đang mở, ngược lại redirect **/orders**.
Menu **Scanning**: mỗi công đoạn có trong cấu hình sản xuất của vendor hiện 1 mục (**Print**, **Cut**, **QC**, **Package**), yêu cầu permission `production.scan` (owner, manager, production). Role staff (PW) không thấy các mục này.
`baseType` không thuộc các công đoạn của vendor → "Công đoạn không tồn tại".

Bố cục: tiêu đề = tên công đoạn, nút **Import hàng loạt**, (trạm QC) nút **Pass** / **Failed**, ô quét, cột trái = artwork sản phẩm, cột phải = panel đơn (**MÃ ĐƠN HÀNG**, danh sách unit, unit vừa quét được highlight) + mã unit + badge trạng thái + lỗi QC đang mở, tiến trình workflow, hướng dẫn công đoạn ("Cách in:", "Cách cắt:", "Cách kiểm tra:", "Cách đóng gói:"), **NOTED:** (note sản xuất), **Phụ kiện master**, **Phụ kiện đi kèm** + **Ghi chú của partner**.

### Quét sub-barcode ghi nhận công đoạn (Print / Cut / Package)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Quét tem trên từng unit để ghi nhận hoàn tất công đoạn hiện tại. |
| Actor | owner, manager, production (`production.scan`) |
| Trigger | Quét sub-barcode + Enter / **Enter barcode**. |
| Pre-conditions | Sub-barcode tồn tại, đã export; unit đang chờ đúng công đoạn của trạm. |
| Post-conditions | Toast "Đã ghi nhận" (hoặc info "Đơn vị này đã hoàn tất công đoạn" nếu đã làm). Nếu đơn vừa xong toàn bộ sản xuất → "Đơn đã xong sản xuất — chuyển sang bước Assize". |
| Main Flow | 1. Placeholder "Quét sub-barcode rồi Enter", hint "Quét tem trên từng sản phẩm, không phải mã đơn".<br>2. Hệ thống tra cứu sub-barcode → unit, item, đơn.<br>3. Xác định công đoạn: công đoạn kế tiếp (hoặc vừa làm) của unit phải trùng loại trạm.<br>4. Ghi nhận công đoạn ngay (không cần bấm xác nhận).<br>5. Hiển thị hướng dẫn công đoạn, note, phụ kiện, tiến trình. |
| Exception Flow | E1. 404 → "Không tìm thấy sub-barcode"; lỗi tra cứu khác → "Ghi nhận thất bại".<br>E2. Đơn đang Error (trừ lỗi artwork từ FF) → "Đơn đang lỗi — không quét được cho tới khi xử lý xong".<br>E3. Item lỗi artwork → "Sản phẩm này đang lỗi artwork — không quét được".<br>E4. Sản phẩm không có công đoạn loại này → "Sai trạm — sản phẩm này không có công đoạn loại này".<br>E5. Unit đang chờ công đoạn khác → "Sai bước — sản phẩm này đang chờ bước {next}".<br>E6. Unit đã xong hết → "Sản phẩm đã xong toàn bộ công đoạn".<br>E7. Lỗi từ API khi ghi nhận: xem bảng Business Rule. |
| Business Rule | Lỗi API ghi nhận:<br>- `sub_barcode_inactive`: "Sub-barcode đã bị hủy"<br>- `sub_barcode_broken`: "Tem này đã hỏng — dùng tem mới: {code}" (hoặc "Tem này đã hỏng và đã có tem thay thế — dùng tem mới")<br>- `order_on_hold`: "Đơn đang bị giữ (on-hold)"<br>- `order_production_closed`: "Đơn đã hoàn tất sản xuất, không quét thêm được."<br>- `sub_barcode_not_exported`: "Chưa export barcode — vào màn Barcode để export trước"<br>- `step_not_in_workflow`: "Công đoạn này không thuộc quy trình của sản phẩm"<br>- `step_out_of_order`: "Phải hoàn tất công đoạn trước đó"<br>- khác: "Ghi nhận thất bại".<br>Công đoạn cố định (assize/label/shipping) không tính trong thứ tự sản xuất. |

### QC Pass

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Ghi nhận unit đạt QC. |
| Actor | owner, manager, production (`production.scan`) |
| Trigger | Ở trạm **QC**: quét sub-barcode rồi click **Pass**. |
| Pre-conditions | Unit đã export barcode, đang chờ bước QC. |
| Post-conditions | Toast "Đã ghi nhận QC đạt" (hoặc "Đơn vị này đã hoàn tất công đoạn"); nếu đơn xong sản xuất → "Đơn đã xong sản xuất — chuyển sang bước Assize". Reset, focus ô quét. |
| Main Flow | 1. Quét sub-barcode → hệ thống chỉ tra cứu, **chưa ghi nhận**.<br>2. Hiển thị unit, badge trạng thái, lỗi QC đang mở (nếu có).<br>3. Click **Pass**. |
| Exception Flow | E1. Unit chưa export → "Chưa export barcode — vào màn Barcode để export trước".<br>E2. Sai bước/sai trạm/xong hết: như UC trên.<br>E3. API: `qc_required` "Bước QC cần chọn Đạt hoặc Lỗi"; `qc_not_applicable` "Bước này không phải QC"; `qc_locked_by_later_step` "Đã quét bước sau, không đổi được kết quả QC"; `qc_order_already_rolled_up` "Đơn đã qua sản xuất, không đổi được kết quả QC". |
| Business Rule | - Nút **Pass**/**Failed** disable khi chưa quét unit hợp lệ hoặc đang gửi.<br>- Trạm QC KHÔNG chặn đơn đang Error / item lỗi artwork ở FE (khác các trạm khác). |

### QC Fail (báo lỗi QC)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Ghi nhận unit lỗi QC, chọn công đoạn gây lỗi, tên lỗi, ảnh. |
| Actor | owner, manager, production (`production.scan`) |
| Trigger | Ở trạm QC, sau khi quét unit, click **Failed**. |
| Pre-conditions | Unit hợp lệ ở bước QC. Danh mục lỗi sản xuất đang active có lỗi áp dụng cho công đoạn. |
| Post-conditions | Toast "Đã ghi nhận lỗi QC"; unit có lỗi QC đang chờ xử lý (xuất hiện ở tab **QC error** của Barcodes). |
| Main Flow | 1. Popup **Failed barcode** – "Nhập lý do sản phẩm không đạt ở bước kiểm tra".<br>2. **Step**: chọn công đoạn đứng trước QC (mặc định công đoạn đầu tiên).<br>3. **Error name**: chọn lỗi trong danh mục (lọc theo công đoạn đã chọn; đổi Step → xoá lựa chọn lỗi).<br>4. Nếu lỗi thuộc loại "Khác" → nhập **Mô tả lỗi**.<br>5. **Quality images**: kéo thả / chọn / dán (Ctrl+V), tối đa 3 ảnh.<br>6. Click **Confirm** → upload ảnh rồi ghi nhận. |
| Alternative Flow | A1. **Huỷ** → đóng popup (không đóng được khi đang gửi). |
| Exception Flow | E1. Không có lỗi cho công đoạn → "Chưa có lỗi nào khai cho công đoạn này. Nhờ quản lý thêm vào danh mục lỗi sản xuất."<br>E2. Không tải được danh mục → "Không tải được danh mục lỗi, thử lại" (nút Confirm disable).<br>E3. Upload ảnh lỗi → "Tải ảnh thất bại, thử lại hoặc gửi không kèm ảnh".<br>E4. API: `qc_blame_step_unknown` "Công đoạn bị lỗi không thuộc quy trình của sản phẩm"; `qc_blame_step_not_before` "Chỉ được đổ lỗi cho công đoạn đứng trước bước QC"; `production_error_not_found` "Không tìm thấy lỗi này, tải lại trang"; `production_error_inactive` "Lỗi này đã ngừng dùng, chọn lỗi khác"; `production_error_step_mismatch` "Lỗi này không áp dụng cho công đoạn đã chọn"; `production_error_other_detail_required` 'Lỗi loại "Khác" cần một mô tả'; QC lock như UC QC Pass. |
| Business Rule | - Danh mục lỗi active được cache 5 phút.<br>- Nếu QC là công đoạn đầu, Step chỉ có công đoạn đầu tiên.<br>- Chỉ nhận file ảnh (image/*); vượt quá 3 ảnh bị bỏ qua. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **Step** * | Bắt buộc, công đoạn trước QC | Chỉ được đổ lỗi cho công đoạn đứng trước bước QC | You can only blame a step that runs before QC |
| **Error name** * | Bắt buộc; lỗi active, áp dụng cho Step | (Nút Confirm disable) / Lỗi này không áp dụng cho công đoạn đã chọn | — / This error does not apply to the selected step |
| **Mô tả lỗi** | Bắt buộc khi lỗi thuộc loại "Khác"; không rỗng sau trim; tối đa 200 ký tự | (Nút Confirm disable) / Lỗi loại "Khác" cần một mô tả | — / An "Other" error needs a description |
| **Quality images** | Tuỳ chọn, chỉ ảnh, tối đa 3 | Tối đa {{max}} ảnh (hint) | Up to {{max}} images |

### Import hàng loạt (bulk scan)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Ghi nhận công đoạn của trạm cho nhiều sub-barcode từ file .xlsx hoặc thư mục ảnh. |
| Actor | owner, manager, production (nút không check permission ở FE ⚠️) |
| Trigger | Click **Import hàng loạt**. |
| Post-conditions | Các mã hợp lệ được ghi nhận công đoạn; đóng popup → refresh sub-barcode các đơn liên quan. |
| Main Flow | 1. Popup **Import hàng loạt**. Trạm QC có notice "Import chỉ ghi nhận QC Đạt. Báo lỗi QC vẫn phải làm ở màn quét tay."<br>2. Chọn nguồn: trạm **Print/Cut** có 2 tab **File sheet** / **Thư mục**; trạm khác chỉ File sheet.<br>3. File sheet: kéo thả .xlsx; **Tải file mẫu** (`bulk-scan-template.xlsx`).<br>4. Thư mục: **Chọn thư mục ảnh** – lấy 20 ký tự cuối tên file làm sub-barcode.<br>5. Preview: thống kê **Tổng / Sẵn sàng / Đã ghi / Bỏ qua / Lỗi**, tab lọc tương ứng, bảng **Sub-barcode / Nguồn / Công đoạn / Đơn / Trạng thái / Lý do**, phân trang ("Trước"/"Sau").<br>6. **Chạy {count} mã** → confirm **Chạy import**: "Sẽ ghi nhận công đoạn cho {count} mã. Không hoàn tác được." → **Xác nhận**.<br>7. Chạy: "Đang chạy… {done}/{total}". Xong: **Import lần mới**, **Tải báo cáo .xlsx** (`bulk-scan-report.xlsx`), **Đóng**. |
| Alternative Flow | A1. **Quay lại** ở preview. A2. **Huỷ** ở confirm. |
| Exception Flow | E1. Lỗi file: xem Validation Rules; khác → "Import thất bại".<br>E2. Lý do dòng: "Không đọc được sub-barcode", "Trùng trong file", "Đã hoàn tất công đoạn này", "Lỗi hệ thống", cùng các lỗi quét ở UC trên (vd "Sai bước — sản phẩm này đang chờ bước {next}", "Tem này đã hỏng — dùng tem mới: {code}").<br>E3. Gián đoạn → "Import bị gián đoạn sau {count} mã — những mã đó ĐÃ được ghi nhận. Tải báo cáo để biết chính xác đã ghi tới đâu rồi import phần còn lại."<br>E4. Không chạy được → "Không chạy được import. Chưa mã nào được ghi nhận, thử lại."<br>E5. Tải mẫu/báo cáo lỗi → "Tải file thất bại". |
| Business Rule | - Thư mục: ảnh mặt trước/sau cùng mã chỉ tính 1 lần; tên file (bỏ đuôi) phải ≥ 20 ký tự và 20 ký tự cuối toàn chữ số, ngược lại dòng lỗi "Không đọc được sub-barcode".<br>- Chỉ dòng Sẵn sàng được chạy; không hoàn tác. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **File sheet** | .xlsx; cột tên "Sub-barcode", dòng 1 là tiêu đề (cột khác bỏ qua) | Không tìm thấy cột "Sub-barcode". File đang có các cột: {{got}} | No "Sub-barcode" column found. The file's columns are: {{got}} |
| **File sheet** | Có ít nhất 1 dòng dữ liệu | File không có dòng dữ liệu nào | The file has no data rows |
| **File sheet** | Đọc được | File không đọc được | The file could not be read |
| **File sheet** | Tối đa 2000 mã | File có {{got}} mã, tối đa {{max}} | The file has {{got}} codes, the maximum is {{max}} |
| **File sheet** | Đã chọn file | Chưa nhận được file — hãy chọn lại file rồi thử lại | No file was received — please pick a file and try again |
| **Trạm** | Hợp lệ | Trạm không hợp lệ | Invalid station |
| **Tên file ảnh** | 20 ký tự cuối (bỏ đuôi) là chữ số | Không đọc được sub-barcode | No sub-barcode in the filename |
| **Sub-barcode** | Không trùng trong file | Trùng trong file | Duplicated in the file |
