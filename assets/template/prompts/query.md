Trả lời câu hỏi chỉ dựa trên second brain này, có dẫn nguồn (dùng cho skill /query và agent ngoài).

1. Đọc CRITICAL.md và INDEX.md (lõi; chỉ mục con theo mảng ở `indexes/`, mở bằng `python3 scripts/brain.py index <mảng>`).
2. Trước khi tra: `python3 scripts/brain.py qa find <câu hỏi>`. Bản "còn hạn" thì dùng lại (vẫn dẫn nguồn của nó);
   "quá hạn"/"nguồn đã đổi" thì đọc lại file nguồn rồi mới trả lời.
3. Tìm theo từ khoá: `python3 scripts/brain.py search <từ>` (xếp hạng BM25, khớp nhất trước). Chọn tối đa 5 file liên quan.
4. Thiếu môi trường/mã/thời gian để trả lời đúng: hỏi lại tối đa 2 câu trước (trừ câu đơn giản), theo
   `50-knowledge/rules/rule-clarify-before-answer.md`.
5. Không có trong vault: nói rõ "chưa có trong brain" kèm lý do (thiếu file/dữ kiện nào), đề xuất nên ingest nguồn nào.
   Không đoán, không báo đã làm/đã hỏi ai khi chưa làm (`50-knowledge/rules/rule-say-no-when-missing.md`).
6. Câu phức tạp (câu hỏi dài, từ 3 nguồn, hoặc trả lời dài): trước khi gửi tự phản biện một lượt: kiểm từng ý với nguồn,
   bỏ phần thừa, ghi mức chắc chắn cuối câu (cao: mọi ý có nguồn / vừa: có ý suy luận / thấp: thiếu nguồn cho ý chính).
7. Trả lời ngắn, cuối câu liệt kê file đã dùng.
