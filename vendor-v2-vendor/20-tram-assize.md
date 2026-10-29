# Trạm Assize

Route: `/production/assize` — Menu **Scanning › Assize**: role staff (nhân sự PW) thấy theo role; role vendor thấy khi có permission `orders.assize` (owner, manager, production). Route không chặn quyền; trong trang các nút không check permission ở FE ⚠️ (BE quyết định).
Staff (staff/admin/super_admin) gọi API nhánh `/api/v1/staff`, vendor gọi `/api/v1`.

Bố cục: tiêu đề **Assize**, nút **Import hàng loạt** (góc phải), ô quét, cột trái = artwork + form **Dimensions**, cột phải = panel đơn (**MÃ ĐƠN HÀNG** `#pwOrderId`, badge partner/status/loại đơn/đơn ghép, danh sách unit + trạng thái). Chưa quét: "Quét một sub-barcode để bắt đầu".

### Quét đơn để Assize

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Quét/nhập mã đơn để tra cứu và mở form nhập kích thước, cân nặng. |
| Actor | staff, owner, manager, production |
| Trigger | Quét barcode / sub-barcode hoặc gõ pwOrderId + Enter (hoặc nút **Enter barcode**). Hoặc mở trang với query `?code=<mã>` (tự tra cứu rồi xoá query). |
| Pre-conditions | Đơn tồn tại, thuộc vendor. |
| Post-conditions | Hiển thị form **Dimensions** của đơn; focus ô **LENGTH**. |
| Main Flow | 1. Placeholder: "Quét barcode / sub-barcode, hoặc gõ pwOrderId"; hint: "Quét barcode đơn, sub-barcode, hoặc gõ pwOrderId rồi Enter".<br>2. Hệ thống tra cứu đơn theo mã.<br>3. Đơn hợp lệ (New/InProduction, đã xong sản xuất) → hiển thị form, điền sẵn dimension cũ (nếu có). |
| Alternative Flow | A1. Đơn đã **Assized** hoặc **Labeled** → toast info "Đơn đã Assized — xem lại dim", form hiển thị read-only ("Đã Assize — read only"). |
| Exception Flow | E1. Đơn Sample/Bulk → "Đơn Sample/Bulk không áp dụng Assize — dùng "Send to Ship" ở màn đơn hàng".<br>E2. Trạng thái khác New/InProduction/Assized/Labeled → "Order chưa ở bước Assize (current: {status})".<br>E3. Đơn New/InProduction nhưng chưa quét xong sản xuất → "Đơn chưa quét xong các công đoạn sản xuất — còn {remaining}/{total} unit" (chỉ đếm item chưa huỷ).<br>E4. 404 → "Order không tìm thấy"; lỗi khác → "Lỗi khi tra cứu order".<br>Mọi lỗi: reset form, focus lại ô quét. |
| Business Rule | - Ô quét tự trim, bỏ qua giá trị rỗng; disable khi đang lưu.<br>- Trạng thái Assize được: New, InProduction. |

### Lưu & mua label (Save & buy label)

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Nhập kích thước/cân nặng, chuyển đơn sang Assized và request label từ Fastway (FW). |
| Actor | staff, owner, manager, production |
| Trigger | Click **Save & buy label ↵** hoặc Enter trong form. |
| Pre-conditions | Đơn đang New/InProduction và đã xong sản xuất. |
| Post-conditions | Đơn → **Assized**; toast "Order {pwOrderId} → Assized — đang request label từ FW"; form reset, focus ô quét. |
| Main Flow | 1. Nhập **LENGTH** (cm), **WIDTH** (cm), **HEIGHT** (cm), **WEIGHT** (g).<br>2. Click **Save & buy label ↵** (đang lưu: "Saving…").<br>3. Hệ thống lưu dimension và request label. |
| Exception Flow | E1. Field không hợp lệ → "Tất cả dimension phải > 0".<br>E2. Lỗi API: `production_incomplete` → "Đơn chưa quét xong các công đoạn sản xuất"; `merged_order_label_from_ff` → "Đơn ghép — label do FF cung cấp, không tự mua label"; `fw_cancel_refused` → "FW từ chối huỷ đơn FW cũ …"; khác → "Có lỗi xảy ra". |
| Business Rule | ⚠️ Việc mua label sau Assize do BE thực hiện (FE chỉ gọi assize). Đơn ghép (merged) chờ FF đẩy label. |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **LENGTH** (cm) | Số, > 0 | Tất cả dimension phải > 0 | Every dimension must be > 0 |
| **WIDTH** (cm) | Số, > 0 | Tất cả dimension phải > 0 | Every dimension must be > 0 |
| **HEIGHT** (cm) | Số, > 0 | Tất cả dimension phải > 0 | Every dimension must be > 0 |
| **WEIGHT** (g) | Số nguyên (step 1, phần thập phân bị cắt), > 0 | Tất cả dimension phải > 0 | Every dimension must be > 0 |

### Cân lại (Re-weigh) ở trạm Assize

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Sửa kích thước/cân nặng của đơn đã Assize; huỷ đơn FW cũ và mua label mới. |
| Actor | staff, owner, manager, production (permission `orders.reweigh` ⚠️ chỉ BE check) |
| Trigger | Click **Re-weigh** khi đơn Assized/Labeled. |
| Pre-conditions | Đơn Assized hoặc Labeled và **không phải đơn ghép**. |
| Post-conditions | Toast "Order {pwOrderId} — đã cân lại, đang huỷ label cũ và mua label mới"; form reset. |
| Main Flow | 1. Click **Re-weigh** → form mở khoá, hint "Cân lại sẽ huỷ đơn Fastway cũ (kể cả label đang chờ) và mua label mới với dimension mới."<br>2. Sửa 4 field.<br>3. Click **Save & re-weigh ↵**. |
| Alternative Flow | A1. **Huỷ** → khôi phục giá trị cũ, form read-only lại. |
| Exception Flow | E1. Field ≤ 0/không phải số → "Tất cả dimension phải > 0".<br>E2. `fw_cancel_refused` → "FW từ chối huỷ đơn FW cũ (hàng đã vào kho hoặc label đã mua với hãng) — không cân lại được. Liên hệ support FW." |
| Business Rule | Đơn ghép (merged) không có nút **Re-weigh**. |

#### Validation Rules
Giống UC **Lưu & mua label**.

### Import Assize hàng loạt

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Assize nhiều đơn từ file .xlsx; mỗi dòng hợp lệ Assize đơn và mua label từ Fastway. |
| Actor | staff, owner, manager, production (nút không check permission ở FE ⚠️; permission `orders.bulk_actions` mô tả "bulk assize") |
| Trigger | Click **Import hàng loạt**. |
| Pre-conditions | File .xlsx đúng mẫu. |
| Post-conditions | Các đơn thành công → Assized + đã mua label. Đóng popup sau khi chạy → refresh danh sách đơn. |
| Main Flow | 1. Popup **Import Assize hàng loạt**, notice "Mỗi dòng chạy được sẽ Assize đơn và mua label từ Fastway — không hoàn tác được."<br>2. (Tuỳ chọn) **Tải file mẫu** (`bulk-assize-template.xlsx`).<br>3. Kéo thả/chọn file .xlsx ("Đang đọc…").<br>4. Màn preview: thống kê **Tổng / Sẵn sàng / Đã Assize / Lỗi**, tab lọc **Tất cả / Sẵn sàng / Đã Assize / Lỗi** (có dòng lỗi → mặc định tab **Lỗi**); bảng **# / pwOrderId / D × R × C (cm) / Nặng (g) / Trạng thái / Chi tiết**.<br>5. Click **Chạy {count} đơn** → confirm **Chạy import Assize**: "Sẽ Assize {count} đơn và tự động mua label từ Fastway. Không hoàn tác được." → **Xác nhận**.<br>6. Chạy tuần tự, hiển thị "Đang chạy… {done}/{total}", từng dòng cập nhật trạng thái.<br>7. Xong: **Import lần mới**, **Tải báo cáo .xlsx** (`bulk-assize-report.xlsx`), **Đóng**. |
| Alternative Flow | A1. **Quay lại** ở preview → chọn file khác.<br>A2. **Huỷ** ở confirm → về preview. |
| Exception Flow | E1. Lỗi file: thiếu cột → "Thiếu cột bắt buộc. File đang có các cột: {got}" (liệt kê tối đa 8 cột); quá dòng → "File có {got} dòng, tối đa {max}"; "File không đọc được"; khác → "Import thất bại".<br>E2. Lý do lỗi từng dòng: "Không tìm thấy đơn", "Đơn không ở trạng thái Assize được" (+ "hiện: {status}"), "Đơn chưa quét xong các công đoạn sản xuất", "Trùng trong file", "Dòng không đọc được", "Lỗi hệ thống".<br>E3. Gián đoạn giữa chừng → "Import bị gián đoạn sau {count} đơn — những đơn đó ĐÃ được Assize và ĐÃ mua label. Tải báo cáo để biết chính xác đã chạy tới đâu rồi import phần còn lại."<br>E4. Không chạy được → "Không chạy được import. Chưa đơn nào được Assize, thử lại." + **Quay lại**.<br>E5. Tải mẫu/báo cáo lỗi → "Tải file thất bại". |
| Business Rule | - Chỉ dòng **Sẵn sàng** được chạy; nút chạy disable khi 0 dòng sẵn sàng.<br>- Không hoàn tác. Đóng popup = reset và huỷ luồng đang chạy (FE ngắt kết nối; ⚠️ BE có dừng hay không chưa xác minh). |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **File** | Chỉ .xlsx | (Bộ chọn file chỉ cho .xlsx) | — |
| **Cột header** | Bắt buộc: pwOrderId, length, width, height, weight (dòng 1 là tiêu đề) | Thiếu cột bắt buộc. File đang có các cột: {got} | Required columns missing. The file has: {got} |
| **Số dòng** | Tối đa 500 dòng | File có {got} dòng, tối đa {max} | The file has {got} rows, max {max} |
| **File** | Đọc được | File không đọc được | The file could not be read |
| **pwOrderId** | Không trùng trong file | Trùng trong file | Duplicate in file |
| **Dòng** | Parse được (⚠️ rule số > 0 do BE) | Dòng không đọc được | Row could not be read |
