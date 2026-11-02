# Kịch bản demo và phạm vi nghiệp vụ

## Chuẩn bị

1. Dùng database **demo riêng**, chạy migration rồi `python backend/manage.py seed`.
2. Seed không reset database đã có tài khoản. Muốn demo sạch, tạo database mới và đổi chuỗi kết nối, không xóa DB đang dùng.
3. Tài khoản `customer`, `staff`, `admin`; mật khẩu sinh ngẫu nhiên tại `backend/instance/demo-accounts.json` trên máy chạy seed. Không đưa tệp này lên GitHub.
4. Có 16 đồ uống, 15 nguyên liệu, 3 size, 3 topping, mức đường/đá, 6 đơn ở 6 trạng thái và phiếu nhập nháp.
5. Dùng cửa sổ riêng cho từng vai trò; sessionStorage tách phiên theo tab. Không dùng tài khoản admin để giả làm khách.

## Demo 1 — Chọn món → giỏ → COD → hoàn tất

- Khách chọn **Cà phê đen đá**, size M, 30% đường, ít đá, trân châu, số lượng 2.
- Giá mỗi ly: 24.000 + 5.000 + 8.000 = **37.000đ**, tổng **74.000đ**.
- Tạo giỏ, tăng/giảm số lượng rồi checkout với người nhận/điện thoại/địa chỉ hợp lệ.
- Đơn `pending`, có snapshot tùy chọn và lịch sử. Tồn kho chưa đổi.
- Staff mở danh sách đơn, **Tải lại đơn**, vào đơn và chuyển `preparing`.
- Kiểm tra tồn giảm đúng công thức + topping và chỉ giảm một lần.
- Staff chuyển `ready`, xác nhận thu COD, `delivering → completed` hoặc hoàn tất tại quầy.
- Admin xem báo cáo: chỉ ghi nhận doanh thu khi đơn hoàn tất **và** đã thu tiền.
- Khách mở lại chi tiết, nhấn **Tải lại trạng thái**, xem đầy đủ timeline.

## Demo 2 — Thiếu nguyên liệu (không nhập tay)

Seed cố ý để **Siro dâu = 0 l**, món **Trà dâu tươi** vẫn còn bán.

- Khách chọn món này, thêm vào giỏ và gửi checkout.
- API trả **409**, chỉ rõ Siro dâu khả dụng 0 và lượng cần thiết.
- Không sinh đơn mới, giỏ giữ nguyên, không trừ tồn, không có tồn âm.
- Admin xem Tổng quan: nguyên liệu dưới ngưỡng và các size Trà dâu tươi có thể pha 0 ly.
- Admin có thể tạm hết món, hoặc tạo phiếu nhập Siro dâu rồi xác nhận và cho khách thử lại.

## Demo 3 — Nhập kho đúng một lần

- Admin → Phiếu nhập, mở phiếu seed `NK-DEMO-001` đang nháp.
- Xem Sữa tươi, Siro đào, Trà đen; tồn chưa tăng ở trạng thái nháp.
- Xác nhận một lần: tồn tăng theo số lượng; có log nhập, người xác nhận và thời gian.
- Phiếu đã xác nhận không sửa được. Gửi lại confirm không tăng kho lần hai.
- Kiểm tra lịch sử xuất nhập và cảnh báo ngưỡng.

## Demo 4 — Hủy trước/sau mốc trừ kho

- Khách đặt đơn rồi hủy khi `pending`: tồn không đổi.
- Staff nhận pha một đơn khác: tồn bị trừ.
- Khách thử hủy sau pha: bị 403.
- Admin hủy với lý do trước khi thu COD: tồn **không hoàn**, lịch sử nêu nguyên liệu đã sử dụng.
- Đơn đã hoàn tất hoặc đã thu COD không được hủy trong phạm vi demo này.

## Demo 5 — Menu/công thức và lịch sử

- Admin sửa tên/giá món đã có đơn; đơn cũ vẫn giữ tên/giá/tùy chọn gốc.
- Ngừng công thức một size: quote/đặt món mới theo size đó bị chặn; khôi phục bằng nút **Khôi phục**.
- Ẩn topping: giỏ mới không chọn được topping này; đơn cũ vẫn đọc được.
- Nguyên liệu đang dùng trong công thức/topping active: không cho ẩn; cần ngừng các công thức/topping liên quan trước.
- Một món+size chỉ có một công thức; công thức đã ẩn phải khôi phục thay vì tạo trùng.

## Demo 6 — Phân quyền và bảo mật

- Khách vào URL quản trị: UI điều hướng về khu vực phù hợp; gọi API quản trị trực tiếp bị 403.
- Staff chỉ xem/xử lý đơn; không thay menu/kho/tài khoản.
- Khách không xem đơn tài khoản khác.
- Admin không tự khóa/hạ quyền tài khoản đang dùng.
- Đăng xuất/đổi mật khẩu/khôi phục mật khẩu thu hồi session.
- Khôi phục qua email cần địa chỉ thật trong hồ sơ và nhà cung cấp Brevo đã cấu hình; email seed `.example` không nhận được thư.

## Mô hình As-Is / To-Be (giả định, không phải khảo sát thực địa)

| Khía cạnh | As-Is mô phỏng | To-Be trong ứng dụng |
|---|---|---|
| Nhận món | Ghi giấy, dễ nhầm tùy chọn | Giỏ có cấu hình, quote server, snapshot đơn |
| Xác nhận nguyên liệu | Nhân viên kiểm tra thủ công | Kiểm tra kho lúc đặt và nhận pha; transaction chống tồn âm |
| Trừ nguyên liệu | Cuối ca khó đối chiếu | Trừ theo công thức khi nhận pha, log từng lần |
| Hủy | Không rõ nguyên liệu đã dùng | Trước pha không trừ; sau pha không hoàn, lưu lý do |
| Nhập kho | Ghi sổ/tồn cộng tay | Phiếu nháp → xác nhận, không cộng trùng |
| Món tạm hết | Báo miệng | Cảnh báo tồn/món rủi ro và admin bật/tắt |

**Nhóm cần tự bổ sung khảo sát có nguồn, phê duyệt giả định và cập nhật SRS theo yêu cầu môn học.**

## In-scope / Out-of-scope

- In: 3 vai trò, menu, tùy chọn, giỏ, COD, luồng trạng thái/hủy, công thức, nguyên liệu/nhập kho, cảnh báo và báo cáo.
- Extra: coupon, audit, reset mật khẩu, kiểm soát request trùng.
- Out: ngân hàng/thẻ thật, bản đồ, giao hàng real-time, dự báo kho/lợi nhuận nâng cao, tích điểm/đề xuất.
- Quy mô demo nhỏ: khóa ghi toàn cục SQL Server; không tuyên bố phục vụ tải lớn.

## Checklist nghiệm thu hosting

- [ ] Backend HTTPS `/api/health` JSON xác nhận SQL Server, không phải HTML SPA.
- [ ] Migration trên SQL cloud, firewall/TLS đúng, dữ liệu seed có chủ đích.
- [ ] CORS GET/POST/Authorization/Idempotency-Key từ Surge.
- [ ] Đăng nhập 3 vai trò từ Surge và đi đủ demo 1–6.
- [ ] Quên mật khẩu tới hộp thư thật, token dùng một lần.
- [ ] Cold start xử lý được; biết quota free và không cam kết SLA 24/7.
- [ ] Không secret trong repo, tài khoản demo đã đổi mật khẩu.
