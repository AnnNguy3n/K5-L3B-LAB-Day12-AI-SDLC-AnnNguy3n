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

Em đã chạy được một ngày từ giỏ rỗng đến đóng quán, tái hiện được bằng input cố định và xem được sổ trên trình duyệt. Bài làm cá nhân chưa có xác nhận về sĩ số và hạn nộp. Em chưa có ticket Phase 2–4 hay kết quả test ẩn để tự chấm theo đề trên lớp.
