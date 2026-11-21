# Hợp đồng tích hợp Phase 1

## Kho từ buổi sáng sang quán

Em dùng một object JSON có đúng một khóa gốc `items`. Mỗi khóa con là một trong bốn nguyên liệu `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`. Số lượng là số nguyên không âm. Kho rỗng được ghi là `{"items":{}}`. Khi xuất kho, chương trình đếm vật phẩm trong giỏ, bỏ mục bằng 0 và sắp khóa theo tên. [File kho mẫu](inventory.sample.json)

- `gather --inventory-out` ghi kho một lần khi có `gather_end`. Cập bến hoặc hết giờ thì giữ số đã nhặt. Theo luật cần triển khai, ngất thì mất giỏ. Dừng ở `tick_limit` trước khi buổi sáng kết thúc thì giữ nguyên file đích.
- `quan --inventory` đọc kho vào `stock` ở tick 0. Nếu vừa truyền file kho vừa khai báo `scenario.quan.stock`, hoặc file sai schema, headless trả mã 2.

## Dữ liệu giữa mô phỏng và giao diện

UI gửi trạng thái phím qua `POST /input` với `move` gồm hai thành phần trong [-1, 1], cùng hai nút boolean `interact` và `catch`. Hai nút tác động ở cạnh nhấn. Buổi sáng dùng trục ngang và độ sâu, buổi tối dùng hai trục trên mặt sàn. `POST /restart` chạy lại cùng seed và scenario.

UI đọc `GET /state` để hiển thị đồng hồ, tiền, uy tín và điểm. Ở buổi sáng, UI đọc `player` (vị trí, oxy, máu), `hold`, `hold_capacity`, `nodes` và `fish`. Ở quán, UI đọc `player`, `stock`, `hand`, `stoves`, `tables` và `customers`. Mọi thay đổi trạng thái đi qua mô phỏng dùng chung với headless.

## Sự kiện

Lớp mô phỏng phát tên và dữ liệu sự kiện. Session thêm `type`, `tick` và `phase`. Headless ghi sự kiện vào JSONL trước snapshot tương ứng. Giao diện đọc danh sách sự kiện gần nhất qua `/state`.

| Nơi phát | Sự kiện | Dữ liệu đã xác định trong starter |
|---|---|---|
| GatherSim | `node_regrown` | `node_id` |
| GatherSim | `gather_end` | `reason`, `inventory` theo schema kho |
| QuanSim | `quan_end` | `reason`, `money`, `earned`, `shift_earned`, `reputation` |
| GatherSim, phần cần làm | `dive`, `surface` | `pos` |
| GatherSim, phần cần làm | `oxygen_empty`, `choke`, `faint`, `gather`, `hold_full`, `fish_caught` | Cần đối chiếu trường dữ liệu với PRD-0. |
| QuanSim, phần cần làm | Các sự kiện về khách đến, chọn món, `customer_left`, `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid` | Cần đối chiếu danh sách đầy đủ, tên và trường dữ liệu với mục E của PRD-0. |
