# Em đối chiếu bài nộp theo tiêu chí chấm

Khi đọc lại PRD-0, TICKET-02 và TICKET-03, em thấy hai giả định làm thay đổi kết quả chơi. Khách vẫn nhận món ở tick kiên nhẫn vừa về 0. Giá sau đổi yêu cầu phụ thuộc độ tươi của từng nguyên liệu lúc bắt đầu nấu. Em sửa hai luật này trên main sau các mốc đã nộp.

| Hạng mục trong README | Em đã kiểm được | Bằng chứng |
|---|---|---|
| Headless · 25 điểm | Chạy hai tiến trình bàn giao kho; file v1.2 giữ ID và độ tươi. Kho đếm cũ bị từ chối ở v1.2. Bộ kiểm 57/57 test đạt, gồm 46 test hồi quy và 11 test mới. Em kiểm đơn ở hạn chót, pause, mua nâng cấp, sinh cá, va chạm và dòng lũ. | [Test theo contract](../../tests/test_campaign_contract.py) · [Log hồi quy](../proof/bo-sung/tests.txt) |
| Làm việc nhóm · 25 điểm | Em làm một mình và khai một người. Git ghi được tiến độ, việc tích hợp và lần đổi yêu cầu. Em chưa có đánh giá chéo hay xác nhận cách tính phần làm việc nhóm cho bài cá nhân. | [TEAM](../../TEAM.md) · [Quyết định đổi kho](../adr/0001-kho-ca-the.md) |
| Kiểm chứng · 15 điểm | Em xuất từng tag sang thư mục tạm, chạy đúng bộ test có tại tag. Bốn mốc lần lượt đạt 41, 43, 45 và 46 test. Các kiểm tra cho bản bổ sung chạy riêng. | [Kết quả theo tag và mã commit](../proof/bo-sung/tags.txt) |
| Harness AI · 10 điểm | Em có lệnh chạy test, lệnh bàn giao kho cũ và lệnh đối chiếu toàn bộ log demo mới. Nhật ký ghi việc em dùng AI và chỗ em phải sửa lại giả định. | [AGENTS](../../AGENTS.md) · [Nhật ký AI](../ai-usage-log.md) |
| Đánh giá và retro · 10 điểm | Em ghi lại bài học về thứ tự tick và cách dựng fixture để nhân vật sống tới lúc dòng lũ kết thúc. | [Retro](../retro.md) · [Phản tư](../members/AnnNguy3n.md) |
| Chất lượng sản phẩm · 10 điểm | Chơi được tối đa năm ngày, mua oxy và máu, theo dõi độ tươi. Em chọn thêm dòng lũ và thử nó ở đúng các mốc bật/tắt. | [Kết quả một và năm ngày](../proof/bo-sung/thoi-gian.txt) · [Manifest](../../game.contract.json) |
| Demo · 5 điểm | Em bắt một cá lóc từ giỏ rỗng rồi nấu, phục vụ và đóng Shop. Log và ảnh cùng cho tổng thu 70k, boa 11k, uy tín 3,2 và điểm 370. | [JSONL](../proof/bo-sung/luot-choi.txt) · [Ảnh cuối lượt](../proof/bo-sung/so-cuoi-ngay.png) |

## Ba bước em dùng để trình bày demo

1. Em chạy `python3 tools/check_submission.py`. Tick 1 bắt được một cá lóc. Khi bắt đầu nấu ở tick 189, cá có ID I1 và độ tươi còn khoảng 98,938.
2. Em tính lại tiền món bằng phần nguyên của 60 × độ tươi / 100, được 59k. Khách trả ở tick 1284, tiền boa là phần nguyên của 59 × 0,2, được 11k.
3. Em kiểm dòng cuối. Lượt chỉ hoàn tất sau khi đóng Shop ở tick 1369. Uy tín 3,2 cho 300 điểm uy tín, cộng 70 tiền thu thành 370 điểm.

Để kiểm thời gian chạy, em dùng seed 1, không điều khiển và chụp snapshot mỗi 600 tick. Một ngày gồm 22.200 tick; năm ngày là 111.000 tick. Thời gian đo trên máy em nằm trong log. Em chưa đo FPS trên máy chấm, chưa có kết quả test ẩn và chưa có ticket Phase 4 để đối chiếu tính năng riêng. Các thay đổi trên main là phần làm bổ sung sau tag.
