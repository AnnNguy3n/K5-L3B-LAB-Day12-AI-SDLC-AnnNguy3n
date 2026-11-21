# Nhật ký thay đổi

## Phase 1

- Em hoàn thiện buổi lặn với oxy, ngạt, hái rau và bắt cá, rồi nối file kho sang ca tối.
- Ở quán, khách gọi món từ nguyên liệu còn đủ. Em thêm các bước giữ nguyên liệu, nấu, bưng món, thanh toán và tính uy tín.
- Em bổ sung chín test, một lượt chơi có thể chạy lại từ đầu và tên món tiếng Việt trên HUD.

## Phase 2

- Em nối buổi sáng và buổi tối trong chế độ chơi trọn ngày trên trình duyệt. R bắt đầu ngày mới với cùng seed.

## Phase 3

- Em thêm đàn cá bơi ngang, quay đầu khi chạm mép và bổ sung đàn theo lịch trong lượt day.

## Phase 4 · v1.0.0

- Em thêm sổ bán hàng cuối ngày, đếm đơn đã thanh toán và tiền boa từ sự kiện trả tiền.
- Em lưu lượt demo có thể chạy lại cùng ảnh sổ cuối ngày và kết quả hồi quy.

## Bổ sung sau v1.0.0

- Em đổi schema kho mặc định từ số lượng sang cá thể có ID, loại và độ tươi. Fixture mới dùng mảng ở gather.hold và quan.stock; kho rỗng có items là mảng rỗng. Em giữ lệnh phát lại v1.0 cho dữ liệu cũ.
- Em sửa đơn hàng và thứ tự cuối tick theo PRD-0. Test cũ cho khách bỏ đi ngay trước thao tác giao món đã được thay bằng test giao thành công đúng hạn.
- Em bổ sung vòng ngày, pause, Shop, kế hoạch năm ngày, cá sấu, đàn cá theo seed và dòng lũ. Demo cuối lượt và ảnh mới được lưu riêng sau các tag đã nộp.
