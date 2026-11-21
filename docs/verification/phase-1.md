# Kiểm chứng Phase 1 · Mốc khởi động

| Nội dung | Cách em kiểm tra | Kết quả |
|---|---|---|
| Repo chung | Tra metadata của fork AnnNguy3n trên GitHub | Repo public, thuộc loại fork. |
| Hồ sơ cá nhân | Đối chiếu TEAM.md, tên repo và cấu hình. Chạy `python3 tools/check_team.py`. | Tên nhóm và số người đã khớp. Công cụ báo một lỗi về sĩ số vì em làm cá nhân, đề yêu cầu 4–6 người. |
| Starter Python | Chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`. | 32/32 test đạt. [Nhật ký chạy test](../proof/phase-1/khoi-dong.txt) |
| Bàn giao kho | Test `test_inv_01_gather_writes_inventory_quan_reads_it` đặt sẵn giỏ có một cá lóc và hai bông súng, cho cập bến rồi mở quán từ file vừa ghi. | Kho đầu ca có đúng hai loại và số lượng ban đầu. [Kết quả test tích hợp](../proof/phase-1/khoi-dong.txt) |

Em mới kiểm được đường truyền kho với giỏ đặt sẵn. Bước tiếp theo là tự hái hoặc bắt cá để tạo kho trong một lượt chơi, sau đó dùng nguyên liệu đó phục vụ khách. Phần đánh giá cuối phase sẽ bổ sung kết quả theo từng tiêu chí của PRD-0.
