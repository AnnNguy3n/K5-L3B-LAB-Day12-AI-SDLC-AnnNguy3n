# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Chạy bài từ một bản clone sạch

```sh
git clone https://github.com/AnnNguy3n/K5-L3B-LAB-Day12-AI-SDLC-AnnNguy3n.git
cd K5-L3B-LAB-Day12-AI-SDLC-AnnNguy3n
python3 -m chonoi.live --mode day --port 0
```

Em dùng Python 3 và thư viện chuẩn. Mở địa chỉ localhost được in ra, bấm **Chơi** để bắt đầu. WASD hoặc phím mũi tên để di chuyển, **E** để hái, cập bến, nấu và phục vụ, **Space** để bắt cá. **P/Esc** tạm dừng. Trong Shop, **1** mua oxy, **2** mua áo phao, **Enter** đóng Shop. **R** bắt đầu lại.

Chạy `sh tools/test_phase1.sh` để kiểm cả bộ test, hoặc `python3 tools/check_submission.py` để phát lại demo hai lần và đối chiếu từng byte. Điểm bằng tổng thu (cả tiền boa) cộng 100 lần phần nguyên của uy tín. Mua nâng cấp trừ tiền hiện có, còn tổng thu được giữ để tính điểm.

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.

## Sáng tạo của nhóm

Em làm thêm dòng nước lũ (`current`) theo TICKET-03. Dòng báo trước ở tick 1680, bắt đầu đẩy nhân vật đủ sâu ở 1800 và hết ở 2280. Em kiểm cả lượt dòng vừa bắt đầu thì hết giờ. [Test dòng lũ](tests/test_campaign_contract.py) · [Kết quả kiểm thử](docs/proof/bo-sung/tests.txt)

## Bản bổ sung trên main

Bốn tag và Release v1.0.0 lưu bài em nộp ban đầu. Trên main, em bổ sung vòng ngày có Shop và kho cá thể theo Test Contract v1.2. Trong demo mới, cá lóc còn 98,938 điểm tươi khi vào bếp. Giá món là 59k, boa 11k, tổng thu 70k và điểm cuối lượt là 370. [Log từng tick sự kiện](docs/proof/bo-sung/luot-choi.txt) · [Ảnh cuối lượt](docs/proof/bo-sung/so-cuoi-ngay.png)

[Đối chiếu tiêu chí chấm](docs/verification/bo-sung.md) · [Báo cáo Phase 1](docs/verification/phase-1.md) · [Phase 2](docs/verification/phase-2.md) · [Phase 3](docs/verification/phase-3.md) · [Phase 4](docs/verification/phase-4.md) · [Retro cá nhân](docs/retro.md)
