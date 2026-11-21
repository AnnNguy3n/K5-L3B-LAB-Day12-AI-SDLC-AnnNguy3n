# Phase 2 · Bàn giao kho trong cùng lượt

Phần dưới ghi kết quả tại tag `phase-2`. Em ghi những thay đổi sau mốc này trong [bảng đối chiếu của bản bổ sung](bo-sung.md).


Em chạy `python3 -m chonoi.live --mode day`. Khi kết thúc buổi sáng, quán nhận kho trong bộ nhớ và bắt đầu ở tick 0. Phím R đưa lượt chơi về buổi sáng ban đầu.

| Tình huống em thử | Kết quả |
|---|---|
| Cập bến với một cá lóc | Kho đầu ca có một cá lóc. Chơi lại đưa em về chế độ gather. |
| Hết giờ với một bông súng | Quán nhận một bông súng. Ở bước tiếp theo, đồng hồ quán tăng lên tick 1. |
| Ngất khi đang mang cá | Quán mở với kho rỗng. |

Em kiểm bằng hai test trong [test_day.py](../../tests/test_day.py) và chạy lại cả bộ test. [Log Phase 2](../proof/phase-2/tests.txt). Đây là phạm vi em tự chọn theo gợi ý trong starter, chưa đối chiếu ticket trên lớp.
