# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 21/11/2026, khởi động | Bài cá nhân được tính phần đóng góp nhóm như thế nào khi đề yêu cầu 4–6 người? | Em khai đúng một thành viên. Cách chấm bài cá nhân còn chờ xác nhận. | Giảng viên |
| 2 | 21/11/2026, khởi động | Các sự kiện còn thiếu trong starter có những trường dữ liệu nào? | Em đã ghi phần xác định được từ mã nguồn. Cần đối chiếu bản đầy đủ trên lab board với mục E của PRD-0 trước khi viết test sự kiện. | Theo PRD-0 |
| 3 | Phase 1, lúc thử giỏ | Giỏ còn một chỗ trong khi một đàn cá cho nhiều đơn vị thì xử lý thế nào? | Em tạm coi một lần bắt là một lần nhận trọn sản lượng. Nếu thiếu chỗ, em giữ nguyên đàn cá và phát `hold_full`. | Giả định của em, chờ đối chiếu PRD-0 |
| 4 | Phase 1, lúc thử quán | Khách hết kiên nhẫn đúng lúc bấm phục vụ thì sao? Món đang nấu hoặc đang cầm thuộc đơn đó được xử lý thế nào? | Em xử lý hết kiên nhẫn trước thao tác. Em thu hồi món của đơn khi khách rời đi. | Giả định của em, chờ đối chiếu PRD-0 |
| 5 | Phase 1, lúc đọc log | Thông tin sự kiện và fixture khách cần khớp đến mức nào? | Em dùng tên có trong starter. Với trường chưa có ví dụ, em lưu tên và dữ liệu thực tế trong log để so lại sau. Em tính boa theo kiên nhẫn lúc phục vụ và cộng tiền, uy tín khi khách ăn xong. | Chờ đối chiếu mục D–G của PRD-0 |
