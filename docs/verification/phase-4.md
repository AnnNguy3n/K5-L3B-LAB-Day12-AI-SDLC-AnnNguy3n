# Phase 4 · Kiểm chứng cuối ngày

Phần dưới ghi kết quả tại tag `phase-4`. Em ghi những thay đổi sau mốc này trong [bảng đối chiếu của bản bổ sung](bo-sung.md).


Em chạy `python3 -m tools.demo_day` từ thư mục gốc. Nhân vật bắt đầu với giỏ rỗng cạnh đàn cá, bắt một cá lóc rồi bơi về bến. Khi vào quán, nhân vật đi từ giữa sàn đến bếp, nấu món, bưng ra bàn và chờ khách ăn xong. Lượt chạy tiếp đến khi đóng cửa. Các lần nhấn phím được ghi trong [kịch bản demo](../../tools/demo_day.py).

| Điều em đối chiếu | Kết quả |
|---|---|
| Nguyên liệu và đơn đã trả | Buổi sáng mang về một cá lóc. Cuối ngày ghi một đơn đã trả. |
| Sổ thu và HUD | Giá món 60k, boa 12k, tổng thu 72k. Uy tín cuối ngày là 3,2 và điểm là 372. Ảnh trình duyệt khớp với dữ liệu mô phỏng. |
| Chơi lại | Sau khi bắt đầu ngày mới, số đơn và boa về 0. Thông tin chuyến sáng trước được xóa. |
| Hồi quy | Em chạy đủ 46 test qua cả bốn mốc. Log có cả test giao tiếp HTTP với cửa sổ chơi. |

[Bảng số liệu](../proof/phase-4/so-ban-hang.json) · [Ảnh sổ bán hàng](../proof/phase-4/so-ban-hang.png) · [Log kiểm thử](../proof/phase-4/tests.txt)

## Tự đánh giá

Em đã chạy được một ngày từ giỏ rỗng đến đóng quán, tái hiện được bằng input cố định và xem được sổ trên trình duyệt. Bài làm cá nhân chưa có xác nhận về sĩ số và hạn nộp. Ở thời điểm gắn tag, em chưa có ticket Phase 2–4 hay kết quả test ẩn để tự chấm theo đề trên lớp.

## Kiểm tra bổ sung trên main

Em muốn biết liệu việc chuyển kho, nhận khách và thanh toán có tiếp tục chạy đúng sau Ngày 5. Em cho bot chơi mười ngày trong cùng một tiến trình. Bot bơi đến hai nút bông súng, hái bằng phím tương tác rồi mang giỏ về bến. Ở quán, bot đến bếp, bưng món ra bàn theo mã đơn và đóng Shop cuối ngày. Em dùng lại kế hoạch D1–D5 từ Ngày 6, còn tiền và uy tín tiếp tục từ ngày trước.

| Phép thử | Kết quả em ghi được |
|---|---|
| 10 ngày liên tục, seed 7 | Hoàn thành 10/10 ngày, 0 lỗi dừng. Ngày nào cũng bàn giao hai bông súng. Sáu ngày có món gỏi trong kế hoạch và đủ nguyên liệu để bán một đơn. Tổng thu 258k, điểm cuối 658. [Kết quả từng ngày](../proof/phase-4/soak.json) |
| Cùng seed và input | Em chạy lệnh trong manifest hai lần. Số ngày, số đơn, số hàng, tiền, uy tín và điểm của từng ngày đều trùng. Em loại thời gian thực thi khi so kết quả. [Test chạy lại](../../tests/test_phase4_submission.py) |
| Khách đang ăn lúc đóng cửa | Em dựng ca chỉ còn một tick. Khách còn 30 tick ăn, giá món 29k và boa 5k. Lệnh headless với phiên bản trong manifest ghi paid rồi quan_end và thu đúng 34k. [Test thanh toán](../../tests/test_phase4_submission.py) |
| Render cảnh sông ở 1280×720 | Chrome headless đã vẽ 1.787 khoảng khung hình trong 30,010 giây, trung bình 59,55 FPS. Khoảng cách giữa hai frame ở phân vị 95 là 17,7 ms. Tick mô phỏng tăng từ 31 đến 1833 trong lúc đo. [Số đo trình duyệt](../proof/phase-4/bench.json) |

Cả bộ đạt **60/60 test**. Ở ca bàn giao riêng, em dùng hai cá thể I2 và I10, trong đó I10 vừa qua ngưỡng ươn lúc cập bến. Snapshot quán ở tick 0 khớp với danh sách trong sự kiện kết thúc buổi sáng, kể cả thứ tự ID, loại và độ tươi. [Log hồi quy v1.3](../proof/phase-4/tests-v1.3.txt)

**Cách em chạy lại** từ thư mục gốc:

```sh
python3 -m chonoi.soak --seed 7 --days 10 --out /tmp/chonoi-soak.json
python3 -m chonoi.bench --seed 42 --duration 30 --out /tmp/chonoi-bench.json
sh tools/test_phase1.sh
```

Em dùng cùng mô phỏng với game thật cho lượt mười ngày. Bot chỉ hái bông súng, nên lần thử này chưa bao phủ các món cá hay cách né cá sấu. Phép đo FPS dùng cảnh sông trên máy em với Chrome và hồ sơ tạm. Em chưa có số đo trên máy chấm hoặc toàn văn TICKET-04 để xác nhận tất cả tiêu chí.
