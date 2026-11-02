# Mây Drinks — React, Flask & Microsoft SQL Server

Ứng dụng bán đồ uống gồm khách hàng, nhân viên pha chế và quản trị. Frontend là React/Vite (Surge chỉ phục vụ tệp tĩnh); API là Flask/Python, lưu dữ liệu trong Microsoft SQL Server. Giao diện hiện tại đọc dữ liệu qua API, **không dùng localStorage làm kho đơn hàng**.

## Tình trạng triển khai

- Backend trên máy phát triển: có thể chạy với SQL Server LocalDB theo hướng dẫn bên dưới.
- Frontend tại [maydrinks.surge.sh](https://maydrinks.surge.sh) chỉ hoạt động trực tuyến khi có **Flask API HTTPS công khai, SQL Server/Azure SQL truy cập được từ hosting và dịch vụ email HTTPS cho khôi phục mật khẩu**. Hiện chưa có tài nguyên cloud được cấp cho dự án; không được coi giao diện Surge là bản hoàn thiện online cho đến khi xác nhận đủ ba điều kiện. Tài khoản demo dùng email `@maydrinks.example` không nhận thư; phải cập nhật email thật trong hồ sơ nếu muốn kiểm thử khôi phục mật khẩu.
- Phương án miễn phí được chọn: Render Free cho API + Azure SQL Database Free cho CSDL + Brevo API HTTPS cho email. Render Free **chặn SMTP các cổng 25/465/587**, do đó không dùng SMTP/587 trong blueprint miễn phí. **Không thể cam kết hoạt động 24/7:** Render Free ngủ sau 15 phút rảnh, có thể mất khoảng một phút để khởi động; Azure SQL Free tự tạm dừng khi rảnh và có thể ngừng đến tháng sau nếu hết quota. Giao diện chờ tối đa 90 giây khi đánh thức backend. Xem [Render Free](https://render.com/docs/free), [Azure SQL Free](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-tier) và [Brevo API](https://developers.brevo.com/reference/send-transac-email).
- Không dùng `https://maydrinks.surge.sh/api` làm API: đây là trang SPA trả HTML. Không dùng localhost hay tunnel tạm làm backend công khai.

## Chạy trên máy phát triển

1. Cài Python 3.12, Node.js 22.12+ (hoặc 24+), Microsoft SQL Server/LocalDB và ODBC Driver 18.
2. Tại thư mục dự án chạy `python -m venv backend/.venv`, `backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt`, `npm ci`.
3. Thiết lập `SQLSERVER_CONNECTION_STRING` bằng chuỗi ODBC trong biến môi trường hoặc `backend/.env` theo `backend/.env.example`. Mặc định dùng LocalDB Windows. Database mới LocalDB cần `init-db` trước Alembic:

```powershell
$env:PYTHONPATH='backend'
backend\.venv\Scripts\python.exe backend/manage.py init-db
backend\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
backend\.venv\Scripts\python.exe backend/manage.py seed
backend\.venv\Scripts\python.exe backend/manage.py serve
```

`seed` tạo tài khoản mẫu và ghi mật khẩu vào tệp **cục bộ** `backend/instance/demo-accounts.json`; không chia sẻ, không commit tệp này. Đổi mật khẩu trước khi công khai. `seed` chỉ được chạy có chủ đích trên database thử nghiệm.

4. Mở terminal khác chạy `npm run dev`; Vite proxy `/api` đến `http://127.0.0.1:8000`. Kiểm tra `http://127.0.0.1:8000/api/health`: phải trả JSON `{"status":"ok","database":"SQL Server"}`.
5. Kiểm thử: `$env:PYTHONPATH='backend'; backend\.venv\Scripts\python.exe -m pytest backend/tests -q`; kiểm tra frontend `npm run lint` và `npm run build`. Trên Windows, pytest tự tạo/xóa database LocalDB riêng và reset seed mỗi test, không sửa dữ liệu demo. Máy khác cần `TEST_SQLSERVER_CONNECTION_STRING` trỏ **database dành riêng** có tên `MayDrinksTest_*`; toàn bộ dữ liệu trong DB test này sẽ bị reset. Tuyệt đối không trỏ test vào production.

## Đối chiếu đề bài và bằng chứng

- [RTM](./docs/requirements-traceability.md): từng G2-FR/USC → API/UI/test, phân biệt local Pass và cloud Pending.
- [ERD & Data Dictionary](./docs/erd-mapping.md): bảng/quan hệ/ràng buộc, giải thích snapshot JSON và các khác biệt vật lý.
- [Kịch bản demo](./docs/demo-scenarios.md): đủ seed, 3 vai trò, thiếu nguyên liệu, nhập kho, hủy trước/sau pha.
- [Kết quả 72 test](./docs/test-results.md): chạy SQL Server thật, gồm cạnh tranh tồn cuối cùng, kho nguyên tử, COD và session.
- [Đề/ERD/use case gốc](./docs/reference/): giữ tài liệu tham chiếu cùng source.

Chưa nghiệm thu Docker Linux, email giao thật hoặc end-to-end public; không coi kết quả local là hoàn thành deployment.

## Triển khai online thực

1. Chủ dự án đăng nhập/tạo tài khoản trên [GitHub](https://github.com), [Render](https://dashboard.render.com/register), [Azure](https://portal.azure.com) và [Brevo](https://www.brevo.com/). Các bước xác minh danh tính, cấp quyền repo, chấp thuận điều khoản/thanh toán phải do chủ tài khoản thực hiện. **Không gửi mật khẩu, khóa API hay chuỗi kết nối qua chat hoặc commit lên Git.** Repo đích: [Fuuron1301/maydrinks](https://github.com/Fuuron1301/maydrinks). Render cần source đã push trước khi tạo deployment; sau khi API hoạt động mới cập nhật Surge.
2. Tạo Azure SQL Database Free hoặc SQL Server TCP/TLS có địa chỉ công khai. Tạo SQL user tối thiểu và cấu hình firewall cho **dải IP outbound của Render**, không chỉ bật “Allow Azure services”. Chuỗi ODBC `SQLSERVER_CONNECTION_STRING` cho production cần `Encrypt=yes;TrustServerCertificate=no`. Kiểm tra hạn mức miễn phí trước khi tạo tài nguyên.
3. Trong Brevo, xác minh email người gửi, bật transactional email và tạo API key. [render.yaml](./render.yaml) dùng `MAIL_MODE=brevo`; trong dashboard Render cài bí mật `SQLSERVER_CONNECTION_STRING`, `BREVO_API_KEY`, `BREVO_SENDER_EMAIL` (địa chỉ đã xác minh). Tạo Blueprint/Web Service Free từ repo theo [Dockerfile](./Dockerfile). Render Free không hỗ trợ SMTP qua 25/465/587. Migration Alembic chạy ở mỗi lần container khởi động và **phải thành công** trước khi Gunicorn nhận request. Render probe `/api/ready` không truy vấn SQL để tránh giữ Azure SQL thức liên tục; `/api/health` mới là kiểm tra SQL thực và sẽ được script deploy gọi.
4. Nạp demo có chủ đích **chỉ trên database thử nghiệm**: trên máy có quyền SQL cloud và đã đặt chuỗi kết nối trong biến môi trường cục bộ, chạy `python backend/manage.py seed`; không nạp demo lên DB thật có dữ liệu. Seed sẽ tạo mật khẩu ngẫu nhiên ở `backend/instance/demo-accounts.json` trên máy thực thi (container miễn phí không có shell bền vững). Không chia sẻ tệp đó; đổi mật khẩu demo ngay sau khi đăng nhập. Nếu không dùng seed, hãy nhập danh mục, sản phẩm, công thức và tài khoản qua quy trình quản trị riêng trước khi triển khai web khách hàng.
5. Xác minh API công khai trả JSON từ SQL Server, danh mục có món thật và CORS chấp nhận Origin `https://maydrinks.surge.sh`. **Chỉ sau đó**, chạy tại thư mục dự án:

```powershell
.\scripts\deploy-surge.ps1 -ApiBase 'https://<backend-domain>/api'
```

Script kiểm tra health, catalog, CORS đăng nhập; kiểm tra xong mới đặt `VITE_API_URL`, build, tạo `dist/200.html` cho React Router và deploy Surge. `VITE_API_URL` chỉ chứa URL công khai, tuyệt đối không chứa khóa bí mật. Nếu chưa có API cloud, script từ chối deploy để không thay bản cũ bằng một trang mới vẫn offline. Trước khi tuyên bố hoàn tất, thử thật từ Surge: đăng nhập, thêm giỏ → COD → cập nhật trạng thái → tồn kho → báo cáo và quên mật khẩu qua email.

## Quy tắc nghiệp vụ chính

- Khách chọn món, size/đường/đá/topping; backend tính giá và định lượng theo công thức SQL Server.
- Giỏ và đơn là dữ liệu server; đặt COD cần Idempotency-Key. Chỉ nhân viên/quản trị có thể đổi trạng thái; trừ nguyên liệu khi bắt đầu pha. Hủy sau khi pha không hoàn nguyên liệu đã sử dụng.
- Báo cáo doanh thu chỉ ghi nhận đơn **hoàn tất và đã thu COD**, không phải mọi đơn đã tạo.
- Ảnh và tài nguyên mẫu ở `public/assets`; bảng ERD/use case thuộc tài liệu gốc ở thư mục cha.

## Cần xác minh thêm trước khi gọi hoàn thiện

Các bài kiểm thử API tự động không thay thế kiểm thử trình duyệt và vận hành hosting. Cần kiểm thử UI responsive, Brevo với email thật, tài khoản đã đổi mật khẩu và giao dịch trên SQL Server cloud. Production đóng connection sau mỗi request để Azure SQL có thể tự pause; Render probe chỉ kiểm tra process. Không gửi ping giữ máy thức hoặc cam kết 24/7 trên gói free.
