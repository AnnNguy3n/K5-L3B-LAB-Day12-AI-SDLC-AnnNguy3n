# 0001 · Giữ ID nguyên liệu từ giỏ tới bếp

Ở bản đầu, một cá lóc trong kho chỉ là một đơn vị đếm. Với TICKET-03, hai con cá lóc có thể cho hai mức giá khác nhau. Em đổi luồng chính sang `{"items":[{"id":"I1","kind":"ca_loc","fresh":100}]}`. Em dùng ID để giữ nguyên liệu cho đơn và trừ tươi trên từng cá thể qua mỗi tick. Em chốt giá lúc bắt đầu nấu, sau đó tiền món giữ nguyên tới lúc trả.

Em tích hợp lần lượt phần đọc kho, mô phỏng buổi sáng, giữ chỗ trong quán, rồi HUD. Bên ghi thay file nguyên tử khi có gather_end. Trong day, hai pha bàn giao dữ liệu trong bộ nhớ cùng tick. File kho đếm cũ thiếu thông tin để biết độ tươi ban đầu, nên v1.2 trả mã 2 khi nhận file đó. Để phát lại bằng chứng trước đây, em giữ preset v1.0 và chạy với `--rules 1.0`.

Em kiểm chuyển đổi bằng hai tiến trình thật. Trong ca quán riêng, em còn đặt trước I1 ở mức tươi 30 và I2 ở 80. Ở bước kế tiếp I1 ươn; bếp dùng I2 và chốt 47k sau một tick hao tươi. [Test kho và giá](../../tests/test_campaign_contract.py)
