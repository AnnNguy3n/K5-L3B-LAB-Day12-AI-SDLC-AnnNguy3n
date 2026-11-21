# Nguyễn Hữu An · Phản tư cá nhân

Em làm bài ở nhà, dùng Codex hỗ trợ viết luật và dựng tình huống kiểm thử. [Phase 1](https://github.com/AnnNguy3n/K5-L3B-LAB-Day12-AI-SDLC-AnnNguy3n/commit/a974b6b) giúp em hiểu vì sao phải theo một con cá từ giỏ đến kho rồi đến lúc khách trả tiền. Test kho ban đầu đặt sẵn nguyên liệu nên chưa kiểm được cả lượt.

Ở [Phase 2](https://github.com/AnnNguy3n/K5-L3B-LAB-Day12-AI-SDLC-AnnNguy3n/commit/054602c), em rà lại ba cách kết thúc buổi sáng. Sang [Phase 3](https://github.com/AnnNguy3n/K5-L3B-LAB-Day12-AI-SDLC-AnnNguy3n/commit/333dc33), em thử bắt F10 rồi kiểm ID của đàn mới và chạy lại cùng seed. Cuối cùng em so [ảnh sổ bán hàng](../proof/phase-4/so-ban-hang.png) với số liệu mô phỏng. Một con cá đem về cho một đơn, thu 72k gồm 12k tiền boa.

Khi đối chiếu PRD-0, em phát hiện khách vẫn nhận món đúng tick hết kiên nhẫn. Em sửa thứ tự xử lý rồi thử lại ở tick đóng cửa. Bản đổi kho cũng làm con cá có giá khác: qua bếp còn khoảng 98,938 điểm tươi, nên món chỉ được 59k và boa 11k. Em thấy việc giữ một kịch bản nhỏ giúp giải thích được vì sao kết quả đổi. [Log bản bổ sung](../proof/bo-sung/luot-choi.txt)
