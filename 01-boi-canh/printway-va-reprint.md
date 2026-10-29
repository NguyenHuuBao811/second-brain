# Printway & Reprint

## Printway
Nền tảng print-on-demand (POD): nhận đơn từ người bán, gửi file thiết kế tới nhà cung cấp (supplier) để in lên áo, cốc, poster, canvas… rồi giao cho khách.

## Reprint là gì
**Reprint** = đơn phải in lại vì sản phẩm lỗi (mờ, lệch màu, sai vị trí in, hỏng khi vận chuyển…). Mỗi reprint tốn thêm chi phí in, vận chuyển và làm chậm giao hàng.

## Mục tiêu tác vụ
Dự đoán **trước khi sản xuất** đơn nào có nguy cơ reprint (`can_in_lai = 1`) để team Ops kiểm tra sớm.

> Lưu ý: chỉ được dùng thông tin **đã biết tại thời điểm đặt đơn**.

## Kinh nghiệm từ team Ops
- File thiết kế độ phân giải thấp thường in ra bị mờ.
- Mỗi xưởng in mạnh/yếu ở những loại sản phẩm khác nhau: một xưởng có thể in áo rất tốt nhưng hay lỗi cốc.
- Đơn gấp in nhiều vị trí dễ lỗi hơn.
