# Từ điển dữ liệu — past.csv / current.csv

- `past.csv`: 1.000 đơn hàng **đã hoàn tất** (01–09/2026), đã biết đơn nào phải in lại.
- `current.csv`: 100 đơn hàng **mới** (10/2026), chưa biết kết quả — cần dự đoán cột `can_in_lai`.

| Cột | Ý nghĩa | Giá trị | Thời điểm ghi nhận |
|---|---|---|---|
| `ma_don_hang` | Mã đơn hàng | PW000001… | Lúc đặt đơn |
| `loai_san_pham` | Sản phẩm được in | ao_thun, ao_hoodie, coc, poster, tranh_canvas | Lúc đặt đơn |
| `cong_nghe_in` | Công nghệ in sử dụng | in_truc_tiep_dtg, in_chuyen_phim_dtf, in_chuyen_nhiet, in_uv | Lúc đặt đơn |
| `do_phan_giai_thiet_ke_dpi` | Độ nét của file thiết kế (DPI càng cao càng nét) | 72, 100, 150, 200, 300 | Lúc đặt đơn |
| `so_vi_tri_in` | Số chỗ được in trên sản phẩm (VD: trước + sau = 2) | 1, 2, 3 | Lúc đặt đơn |
| `la_don_gap` | Khách có yêu cầu giao gấp không | 1 = gấp, 0 = thường | Lúc đặt đơn |
| `nha_cung_cap` | Xưởng in nhận sản xuất đơn | NCC_A … NCC_O (15 xưởng) | Lúc đặt đơn |
| `so_ngay_giao_tre` | Số ngày xưởng giao trễ so với cam kết | 0, 1, 2… | **Sau khi đơn hoàn tất** (đã tính cả thời gian in lại nếu có) |
| `can_in_lai` | **Nhãn cần dự đoán**: đơn có phải in lại không | 1 = phải in lại, 0 = không | Sau khi đơn hoàn tất — **chỉ có trong past.csv** |
