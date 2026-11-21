# Kiểm chứng Phase 1 · Nguyễn Hữu An

Em bắt đầu với giỏ rỗng và đặt một đàn cá lóc gần bến để lượt thử ngắn, dễ làm lại. Sau khi bắt cá và cập bến, em dùng đúng file kho vừa xuất để mở quán. Cá lóc bán được 60, khách boa 12. Cuối ca tiền là 72, uy tín 3,2 và điểm 372.

| Nội dung | Cách em kiểm | Kết quả và bằng chứng |
|---|---|---|
| Khởi động | Em kiểm fork, khai báo một thành viên và chạy bộ test của starter. | Repo là fork public. 32/32 test đạt. Công cụ kiểm danh sách vẫn báo thiếu sĩ số theo đề. [Log ban đầu](../proof/phase-1/khoi-dong.txt) |
| Bơi, lặn và oxy | Em cho nhân vật bơi qua ngưỡng mặt nước rồi quay lại. Ở lượt khác, nhân vật mang cá trong giỏ và chỉ còn một máu khi hết oxy. | Ghi được cả hai sự kiện lặn và nổi. Khi ngất, giỏ rỗng và chỉ có một sự kiện kết thúc lượt. [Nhóm test GatherRules](../../tests/test_phase1.py) |
| Hái và bắt cá | Em đặt hai nút N2 và N10 cùng vị trí, cho mọc lại cùng tick. Em cũng thử bắt cá linh khi giỏ chỉ còn một chỗ và bấm bắt cá lần hai trong hồi chiêu. | N2 được hái trước N10. Khi thiếu chỗ, đàn cá còn nguyên. Lần bấm trong hồi chiêu không thêm cá vào giỏ. [Log test](../proof/phase-1/test-cuoi-phase.txt) |
| Bàn giao kho | Ở tick 1 em bắt được cá. Tick 35 nhân vật nổi lên. Tick 68 em cập bến. | File kho chứa đúng một cá lóc, snapshot đầu ca quán cũng có đúng một cá lóc. [Lượt sáng](../proof/phase-1/gather-log.txt) · [Kho](../proof/phase-1/kho.json) |
| Nấu và phục vụ | Em đối chiếu sự kiện ở bếp và bàn T1. | Khách tới ở tick 120, bắt đầu nấu ở 121, chín ở 481, lấy món ở 482 và phục vụ ở 616. Khách trả tiền ở tick 1216. Cuối ca kho trống, bếp trống và bàn trống. [Lượt tối](../proof/phase-1/quan-log.txt) |
| Khách bỏ đi và kho thiếu | Em thử phục vụ ngay ở tick khách hết kiên nhẫn, mở quán khi kho rỗng và nạp đơn giữ nguyên liệu vượt tồn. | Khách rời bàn trước thao tác phục vụ. Kho rỗng phát no_dish. Đơn mâu thuẫn bị từ chối khi dựng mô phỏng. [Nhóm test QuanRules](../../tests/test_phase1.py) |
| Chạy lại cùng seed | Em chạy cả hai chế độ hai lần với cùng bộ input và seed 1. | Hai log buổi sáng giống nhau từng byte. Hai log buổi tối cũng vậy. Tổng cộng 41/41 test đạt, gồm 32 test starter và 9 test bổ sung. [Kết quả cuối phase](../proof/phase-1/test-cuoi-phase.txt) |
| Giao diện | Em mở một ca riêng có một cá lóc trong kho để quan sát HUD lúc khách chờ. | Ảnh hiện tên “Cá lóc nướng trui”, thanh kiên nhẫn, số cá trong kho, tiền, uy tín và điểm. [Ảnh HUD](../proof/phase-1/hud-quan.png) |

## Cách em chạy lại

Từ thư mục gốc, em chạy hai lệnh sau. Lệnh thứ hai in ra thư mục chứa kho và hai log mới. Các file đầu vào em dùng nằm trong [bộ tình huống Phase 1](../../tests/fixtures/phase-1/).

```sh
sh tools/test_phase1.sh
sh tools/replay_phase1.sh
```

## Phần còn mở

Em đã kiểm các luật trên theo starter và cấu hình trong repo. Em chưa có bản PRD-0 trên lớp để đối chiếu từng trường của sự kiện, thứ tự ưu tiên và toàn bộ tiêu chí chấm ẩn. Em ghi các cách xử lý đang dùng vào [sổ câu hỏi](../clarify.md). Phần sĩ số của bài cá nhân vẫn chờ giảng viên xác nhận.
