# Quy trình dự đoán Reprint

## Các bước

1. Lấy ngẫu nhiên 100% đơn hàng từ quá khứ (`past.csv`) để nghiên cứu.
2. Loại bỏ 2 cột mã đơn hàng và số nngayf giao trễ
3. Dùng rules / model có hiệu quả tốt nhất để điền cột `can_in_lai` (0/1) cho `current.csv`.
4. Ghi bài học mới vào `04-bai-hoc/bai-hoc.md`.
5. Zip `current.csv` (đã có cột `can_in_lai`) và thư mục `second-brain/` thành `Team-ID-Ten-nhom.zip`.