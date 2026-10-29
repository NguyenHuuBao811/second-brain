Chạy eval second brain này. Đọc eval/golden.jsonl và eval/golden-lark.jsonl (nếu có) (mỗi dòng: q, expected_pages, answer).
Với mỗi q: trả lời CHỈ dùng vault, ghi cited_pages. Không có trong vault thì ghi "không có trong brain".
Chấm: hit (expected ⊂ cited; expected kết thúc bằng `/` nghĩa là bất kỳ file nào trong thư mục đó), correct 0-1, faithful 0-1.
Câu có answer rỗng (chưa có đáp án chuẩn): chỉ chấm hit và có/không trả lời được, bỏ correct.
In bảng tổng (tách 2 bộ golden và golden-lark) + danh sách câu sai kèm page còn thiếu. Ghi eval/results-<hôm nay>.md. Không sửa vault.
