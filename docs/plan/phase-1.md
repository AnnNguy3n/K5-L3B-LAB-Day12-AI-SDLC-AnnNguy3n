# Kế hoạch Phase 1 · Nguyễn Hữu An

Em dùng starter Python để làm cả hai chế độ. Mục tiêu cuối phase là mang nguyên liệu từ buổi sáng sang quán, nấu và phục vụ được một đơn. Em phụ trách cả mô phỏng, giao diện và kiểm thử.

| Mốc dự kiến từ đầu buổi | Công việc | Điều kiện để chuyển bước |
|---|---|---|
| 0:00–0:15 | Khai báo thành viên, kiểm tra fork, thống nhất định dạng kho, giao diện và chạy test ban đầu. | Quán đọc đúng kho mà buổi sáng đã ghi. |
| 0:15–0:30 | Làm luật oxy, ngạt, ngất và giỏ. Sau đó xử lý hái, mọc lại, bắt cá và hồi chiêu. | Kiểm giỏ và kho trong ba trường hợp cập bến, hết giờ và ngất. |
| 0:30–0:45 | Dùng kho mẫu để làm khách đến, chọn món và giữ nguyên liệu. Tiếp tục với bếp, bưng món, thanh toán và uy tín. | Theo được một đơn từ lúc khách đến đến lúc trả tiền. |
| 0:45–trước 1:00 | Chạy lượt liên thông, kiểm tra HUD, đối chiếu tiêu chí PRD-0 và lưu bằng chứng. | Ghi từng mục đạt hoặc còn thiếu trước khi gắn tag `phase-1`. |

Em ưu tiên luật và dữ liệu headless trước phần hình ảnh. Rủi ro chính là sai thứ tự sự kiện trong cùng một tick và tính hai lần nguyên liệu đã giữ. Em sẽ kiểm hai trường hợp này bằng scenario nhỏ với seed cố định. Các điểm cần xác nhận được ghi trong [sổ câu hỏi](../clarify.md).
