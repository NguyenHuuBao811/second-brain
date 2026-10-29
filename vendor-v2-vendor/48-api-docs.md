# API docs

Route: `/api-docs` — Menu: nhóm **Quản lý** → **API docs**, chỉ hiện khi vendor được bật API (**apiAccessEnabled**) **và** user là **owner**. Trang **không yêu cầu đăng nhập**: có đăng nhập → hiện trong layout có sidebar; chưa đăng nhập → hiện trang trơn. API key do admin cấp ở màn chi tiết vendor phía admin.

### Xem tài liệu Open API

#### UC Description
| Mục | Nội dung |
|---|---|
| Description | Tài liệu tích hợp hệ thống của vendor với Vendor Mini App qua HTTP. |
| Actor | owner (qua menu); bất kỳ ai có link |
| Trigger | Vào menu **API docs** hoặc mở `/api-docs`. |
| Main Flow | 1. Tiêu đề **API docs** + badge trạng thái (chỉ với user vendor đã đăng nhập): "API đang bật" / "API đang tắt cho vendor này". Intro: "Tích hợp hệ thống của bạn với Vendor Mini App qua HTTP. Mọi request gửi kèm API key do quản trị viên cấp."<br>2. **Base URL** = domain đang mở app.<br>3. **Xác thực**: gửi key qua header `X-API-Key: vma_live_…`; không gửi qua query string; key hết hạn / bị tạo lại → 401.<br>4. 4 endpoint (method, path, **Tham số**, **Request mẫu** curl, **Response mẫu**) — bảng dưới.<br>5. **Đối tượng Order**: JSON mẫu + bảng **Field liên quan đến label**.<br>6. **Mã lỗi**: format lỗi + bảng HTTP / Mã / Ý nghĩa. |
| Business Rule | - Giới hạn **120 request/phút/key**; vượt → 429.<br>- Tham số `{ref}` nhận: UUID đơn, mã đơn PW, mã đơn FF, tracking number, hoặc barcode in trên hàng.<br>- Mọi endpoint trả cùng đối tượng Order (cùng field, items, labels).<br>- ⚠️ Trang public: ai có link đều đọc được tài liệu (không lộ key). |

#### Endpoint
| Tên | Method & Path | Tham số | Rule |
|---|---|---|---|
| **Danh sách đơn** | `GET /api/v1/open/orders` | status, search, createdFrom, createdTo, limit=50, offset=0, sort=createdAt\|dueDate, order=desc\|asc | Đơn của vendor, mới nhất trước. search: một/nhiều mã đơn PW/FF, cách nhau dấu phẩy, khớp một phần — không tìm theo tracking/barcode. createdFrom/To dạng YYYY-MM-DD giờ VN. limit tối đa 100. |
| **Chi tiết đơn** | `GET /api/v1/open/orders/{ref}` | ref | Trả đơn kèm items và lịch sử label. |
| **Assize đơn** | `PUT /api/v1/open/orders/{ref}/assize` | length, width, height (cm, > 0) · weightGrams (g, số nguyên 1–99999) | Chuyển đơn sang Assized. Chỉ khi đơn ở New/InProduction và mọi bước sản xuất đã xong. Tự yêu cầu mua label như trên app. Không đủ điều kiện → 409. |
| **Cân lại đơn** | `PUT /api/v1/open/orders/{ref}/reweigh` | như Assize | Cho đơn đã assize, kể cả khi label đang chờ Fastway hoặc đã có. Huỷ đơn Fastway cũ, mua label mới; tracking cũ bị xoá tới khi label mới về. Đơn chưa assize hoặc đơn ghép → 409. |

#### Field liên quan đến label
| Field | Ý nghĩa |
|---|---|
| `latestLabelError` | Lỗi lần mua label mới nhất `{ status: failed \| timeout, reason }`; null nếu không lỗi. Sửa rồi gọi /reweigh để mua lại. |
| `labels[]` | Lịch sử mọi lần mua label, mới nhất trước. |
| `labels[].status` | requested · in_flight · fulfilled · failed · timeout · superseded · canceled. |
| `labels[].failureReason` | Lý do thất bại nguyên văn từ hãng vận chuyển. |
| `labels[].dimension` | Kích thước (cm), cân nặng (g) dùng để mua label đó; có thể khác order.dimension nếu đã cân lại. |
| `labels[].requestedAt` / `fulfilledAt` | Thời điểm gửi yêu cầu / nhận label (null nếu chưa có). |
| `serviceCode` | Mã dịch vụ vận chuyển, theo quốc gia nhận. |
| `labelPurchasedAt / shippedAt` | Thời điểm đơn có label / giao cho hãng vận chuyển. |

#### Mã lỗi
Mọi lỗi trả JSON `{ error, details }`; lỗi xác thực và không tìm thấy đơn có mã ở `details.code`.

| HTTP | Mã | Ý nghĩa |
|---|---|---|
| 401 | `api_key.missing` | Thiếu header X-API-Key |
| 401 | `api_key.invalid` | Key không đúng hoặc đã bị tạo lại |
| 401 | `api_key.disabled` | API đang tắt cho vendor |
| 401 | `api_key.expired` | Key đã hết hạn |
| 403 | `api_key.vendor_inactive` | Vendor đang bị khoá |
| 404 | `order.not_found` | Không tìm thấy đơn của vendor với mã này |
| 409 | — | Đơn chưa ở trạng thái cho phép assize (sai status, chưa xong sản xuất, đã huỷ, đã hoàn phí ship, đơn sample/bulk). Lý do ở `error` (vd. production_incomplete); `details.currentStatus` = status hiện tại, `details.requiredStatus` khi lỗi do sai status. |
| 400 | — | Tham số hoặc body không hợp lệ |
| 429 | — | Vượt giới hạn request |

#### Validation Rules
| Field | Validation Rule | Error Message (VI) | Error Message (EN) |
|---|---|---|---|
| **length / width / height** | Số > 0 (cm). | 400 — "Tham số hoặc body không hợp lệ" | 400 — "Invalid parameters or body" |
| **weightGrams** | Số nguyên 1–99999 (g). | như trên | như trên |
| **limit** | ≤ 100. | như trên | như trên |
| **createdFrom / createdTo** | YYYY-MM-DD (giờ VN). | như trên | như trên |
