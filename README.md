# Mây Drinks — React · Flask · Microsoft SQL Server

Ứng dụng bán đồ uống cho **khách hàng, nhân viên pha chế và quản trị**.
Dữ liệu menu, giỏ, đơn, công thức và kho được lưu trong **Microsoft SQL Server**;
không có chế độ giả lập localStorage hoặc tự chuyển sang SQLite.

**Phạm vi bản nộp:** chạy đầy đủ trên máy Windows với SQL Server LocalDB/Express.
Deploy cloud được hoãn theo kế hoạch của chủ dự án; cấu hình SQL Server trên AWS sẽ làm riêng.
Trang [Surge cũ](https://maydrinks.surge.sh) **không phải bằng chứng backend online**.
Không dùng `https://maydrinks.surge.sh/api` làm API vì địa chỉ đó trả HTML của frontend.

## 1. Chức năng và tài liệu đối chiếu

- Đăng ký, đăng nhập/đăng xuất, hồ sơ, đổi/quên mật khẩu; phân quyền API và UI.
- Danh mục/đồ uống, giá, ảnh, size, đường, đá, topping; tìm kiếm và giỏ server.
- Báo giá server, checkout COD, snapshot cấu hình, chống đặt trùng khi retry.
- Trạng thái đơn, lịch sử, hủy theo quyền; ghi nhận thu COD.
- Nguyên liệu, công thức từng món+size, phiếu nhập, kiểm kê và lịch sử tồn.
- Kiểm tra thiếu nguyên liệu, trừ kho một lần khi nhận pha, không cho tồn âm.
- Cảnh báo dưới ngưỡng/món nguy cơ hết; báo cáo doanh thu, đơn, bán chạy, tiêu hao.
- Bổ sung mã giảm giá và nhật ký thao tác.

| Tài liệu | Nội dung |
|---|---|
| [RTM yêu cầu](docs/requirements-traceability.md) | FR01–12 / USC01–10 → API, UI, test và kết quả local |
| [ERD & Data Dictionary](docs/erd-mapping.md) | Bảng/quan hệ/ràng buộc, khác biệt vật lý, state/sequence diagram |
| [Kịch bản demo](docs/demo-scenarios.md) | 6 luồng nghiệm thu, dữ liệu mẫu, giả định, phạm vi |
| [Kết quả kiểm thử](docs/test-results.md) | Danh sách test thực tế, môi trường, lệnh chạy và giới hạn |
| [Đề và sơ đồ gốc](docs/reference/) | PDF đề bài, ERD và use case để đối chiếu |

PDF cho phép tên bảng/cột khác sơ đồ nếu đủ dữ liệu và quy tắc.
Các khác biệt như role cố định và JSON snapshot được ghi rõ trong tài liệu ERD,
không khẳng định schema giống nguyên văn sơ đồ.

## 2. Yêu cầu máy cá nhân

- **Windows 10/11 64-bit**, PowerShell, Git.
- **Python 3.13** (đã kiểm thử với 3.13.3), pip và venv.
- **Node.js 22.12+ hoặc 24+**, npm (đã kiểm thử với Node 24.18.0).
- **Microsoft SQL Server 2022 LocalDB** hoặc SQL Server Express/Developer đang chạy.
- **Microsoft ODBC Driver 18 for SQL Server** 64-bit.
- SSMS là tùy chọn để xem bảng và chạy truy vấn; **cài SSMS không đồng nghĩa đã cài SQL Server**.

Nguồn cài: [Python](https://www.python.org/downloads/), [Node.js](https://nodejs.org/),
[SQL Server](https://www.microsoft.com/en-us/sql-server/sql-server-downloads),
[LocalDB](https://learn.microsoft.com/en-us/sql/database-engine/configure-windows/sql-server-express-localdb),
[ODBC Driver](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server),
[SSMS](https://learn.microsoft.com/en-us/ssms/install/install).

Các lệnh sau chạy trong **thư mục chứa README này**, không phải thư mục `backend`.
Mở terminal trực tiếp tại thư mục dự án; không cần kích hoạt venv hay đổi ExecutionPolicy.

## 3. Cài dependencies và cấu hình local

Nếu lấy bản mới từ GitHub:

```powershell
git clone https://github.com/Fuuron1301/maydrinks.git
```

Mở thư mục clone bằng IDE, rồi mở terminal ở thư mục đó:

```powershell
python --version
node --version
python -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm ci
if (!(Test-Path backend/.env)) { Copy-Item backend/.env.example backend/.env }
```

Kiểm tra driver đã được cài trên hệ điều hành:

```powershell
.\backend\.venv\Scripts\python.exe -c "import pyodbc; print(pyodbc.drivers())"
```

Danh sách phải có `ODBC Driver 18 for SQL Server`.
Cài gói `pyodbc` bằng pip **không thay thế** việc cài driver Microsoft.

### Cách A — LocalDB, đơn giản nhất cho Windows

Giữ các giá trị sau trong [backend/.env](backend/.env.example):

```dotenv
APP_ENV=development
SQLSERVER_SERVER='(localdb)\MSSQLLocalDB'
SQLSERVER_DATABASE=MayDrinks
MAIL_MODE=file
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Không đặt `SQLSERVER_CONNECTION_STRING` khi dùng cách A/B.
Nếu instance LocalDB chưa chạy, dùng `SqlLocalDB start MSSQLLocalDB`.
Nếu lệnh không có trong PATH, executable SQL Server 2022 thường nằm tại
`C:\Program Files\Microsoft SQL Server\160\Tools\Binn\SqlLocalDB.exe`.

### Cách B — SQL Server Express, Windows Authentication

Trong cùng file môi trường, chỉ thay server theo instance đã cài:

```dotenv
SQLSERVER_SERVER='.\SQLEXPRESS'
SQLSERVER_DATABASE=MayDrinks
```

Dịch vụ SQL Server phải chạy; Windows user hiện tại cần quyền tạo database
cho bước `init-db`. Database/API/migration/seed đều dùng chung cấu hình này.

### Cách C — SQL Authentication / SQL Server remote

Mở SSMS, tạo database **MayDrinks** rỗng và cấp quyền thích hợp cho SQL login.
Đặt chuỗi ODBC đầy đủ trong `backend/.env`, ví dụ cấu trúc:

```dotenv
SQLSERVER_CONNECTION_STRING='DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost,1433;DATABASE=MayDrinks;UID=maydrinks_app;PWD=replace-locally;Encrypt=yes;TrustServerCertificate=yes;'
```

Thay user/mật khẩu/server bằng giá trị trên máy, không dùng nguyên ví dụ.
Chuỗi đầy đủ **ưu tiên hơn** `SQLSERVER_SERVER`/`SQLSERVER_DATABASE`.
**Bỏ qua `init-db` ở cách C**: CLI chủ động từ chối để không tạo nhầm database
trên một server khác. Tiếp tục từ lệnh Alembic bên dưới.
Với SQL cloud phải dùng TLS hợp lệ (`TrustServerCertificate=no`) và giới hạn firewall.
Không commit mật khẩu/chuỗi thật; biến môi trường của terminal ưu tiên hơn `.env`.

## 4. Tạo bảng, dữ liệu mẫu và kiểm tra backend

Với cách A/B, tạo database trước:

```powershell
.\backend\.venv\Scripts\python.exe backend/manage.py init-db
```

Sau đó, cho cả A/B/C:

```powershell
$env:PYTHONPATH='backend'
.\backend\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.\backend\.venv\Scripts\python.exe backend/manage.py seed
.\backend\.venv\Scripts\python.exe backend/manage.py check
```

Lệnh `check` phải báo `SQL Server connection: OK`, revision `fc2a96045963 (head)`
và trên database mới có **16 drinks, 15 ingredients, 5 orders**.
Seed cũng tạo 3 size, 3 topping, công thức, 5 trạng thái đơn và phiếu nhập nháp.
**Siro dâu = 0** là dữ liệu cố ý để demo chặn đơn thiếu nguyên liệu, không phải lỗi seed.

`seed` không reset dữ liệu và không đổi mật khẩu database đã có tài khoản.
Nếu muốn demo sạch, tạo **database demo mới**, cấu hình lại rồi migration/seed;
không xóa database đang dùng. Không tự ý dùng `drop_all`/downgrade trên dữ liệu thật.

### Tài khoản demo

Sau lần seed đầu, mật khẩu ngẫu nhiên được ghi **chỉ trên máy đó** tại
`backend/instance/demo-accounts.json` (đã bị Git bỏ qua).

```powershell
Get-Content -Encoding UTF8 backend/instance/demo-accounts.json
```

| Username | Vai trò | Khu vực |
|---|---|---|
| `customer` | Khách hàng | Chọn món, giỏ, đặt/hủy/xem đơn của mình |
| `staff` | Nhân viên | Xem và xử lý tiến trình đơn, thu COD |
| `admin` | Quản trị | Menu, kho, công thức, phiếu nhập, báo cáo, tài khoản |

Tên hồ sơ admin mặc định là **Hà Linh**; đó vẫn là tài khoản `admin`, không phải đăng nhập nhầm.
Mật khẩu từ máy khác/lần seed khác không được đảm bảo dùng lại.
Dùng tab/cửa sổ riêng cho từng vai trò, đổi mật khẩu trước khi mở ra Internet.

## 5. Chạy ứng dụng — 2 terminal

**Terminal 1 — API Flask qua Waitress:**

```powershell
.\backend\.venv\Scripts\python.exe backend/manage.py serve
```

**Terminal 2 — giao diện React/Vite:**

```powershell
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Mở **http://127.0.0.1:5173**. Để cả hai terminal chạy trong lúc demo.
Dừng bằng `Ctrl+C`; mở lại chỉ cần chạy 2 lệnh trên, không seed lại.

Kiểm tra trong terminal thứ ba hoặc trình duyệt:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:5173/api/health
```

Cả hai phải trả `status=ok`, `database=SQL Server`.
Vite proxy `/api` đến port 8000; không cần chỉnh URL API khi chạy local.
Để `VITE_API_URL` trống/không khai báo trong `.env*` ở root.
Không mở trực tiếp `index.html` bằng `file://`, không dùng Live Server thay Vite.
`/api/ready` chỉ kiểm tra process; **`/api/health` mới kiểm tra kết nối SQL**.

## 6. Quên mật khẩu khi demo offline

Với `MAIL_MODE=file`, tính năng không cần tài khoản email thật:

1. Dùng email hồ sơ của tài khoản (ví dụ `customer@maydrinks.example`) ở form Quên mật khẩu.
2. Backend tạo thư `.eml` trong `backend/instance/mail-outbox/`.
3. Mở thư mới nhất bằng ứng dụng đọc email, hoặc xem nội dung UTF-8 để lấy link reset.
4. Link có hiệu lực 15 phút, dùng một lần; đổi xong đăng nhập bằng mật khẩu mới.

Đây là **outbox local**, không phải gửi email Internet. Không commit thư/token.
`FRONTEND_URL` phải trỏ đúng frontend đang chạy. Email gửi thật qua SMTP/Brevo là tùy chọn,
chưa được nghiệm thu delivery trong bản nộp local.

## 7. Kiểm thử và xem SQL bằng SSMS

```powershell
$env:PYTHONPATH='backend'
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q --junitxml=backend/instance/test-results.xml
npm run lint
npm run build
```

Trên Windows, pytest tạo database LocalDB **MayDrinksTest_<random>** riêng,
chạy Alembic, reset seed từng test và xóa DB tự tạo khi xong.
Không sửa database `MayDrinks` đang demo. Nếu chỉ cài Express hoặc chạy ngoài Windows,
tự tạo DB tên **MayDrinksTest_<tên>** và đặt `TEST_SQLSERVER_CONNECTION_STRING`
trỏ đúng DB đó trước khi chạy. **Toàn bộ bảng nghiệp vụ trong DB test chỉ định sẽ bị reset**;
DB chỉ định không tự bị xóa. Không bao giờ dùng dữ liệu demo/production cho biến này.

Kết quả được lưu tại [docs/test-results.md](docs/test-results.md).
Các test trùng lặp cũ đã gộp vào 2 module: acceptance nghiệp vụ và configuration.

Trong SSMS: Server type `Database Engine`, server `(localdb)\MSSQLLocalDB`
(hoặc instance đã cấu hình), Authentication `Windows Authentication`, database `MayDrinks`.
Có thể kiểm tra:

```sql
SELECT version_num FROM alembic_version;
SELECT COUNT(*) AS drinks FROM drinks;
SELECT COUNT(*) AS ingredients FROM ingredients;
SELECT status, COUNT(*) AS orders FROM orders GROUP BY status;
SELECT name, quantity, unit, minimum FROM ingredients ORDER BY name;
```

Nếu cần file DDL để đọc/nộp bổ sung, xuất trực tiếp từ migration (không chỉnh hai nguồn schema):

```powershell
.\backend\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head --sql | Out-File -Encoding utf8 backend/instance/schema.sql
```

File này là **schema rỗng**, không chứa dữ liệu seed. Quy trình chuẩn vẫn là Alembic online;
không chạy lại DDL trên database đã migration.

## 8. Xử lý lỗi thường gặp

| Hiện tượng | Kiểm tra/cách xử lý |
|---|---|
| `IM002` / không tìm thấy driver | Cài Microsoft ODBC Driver **18** 64-bit, kiểm tra `pyodbc.drivers()` |
| Không tìm thấy LocalDB/instance | Cài SQL Server thực sự, start instance, kiểm tra tên server trong `.env` |
| Login failed / không mở được database | Kiểm tra Windows/SQL login, quyền truy cập, tên DB; chạy `init-db` đúng cách A/B |
| `Invalid object name` / schema chưa hiện hành | Chạy Alembic `upgrade head` rồi `manage.py check` trước seed/serve |
| API đang offline / Vite `ECONNREFUSED` | Chạy backend ở port 8000, kiểm tra `/api/health`; frontend không tự sinh dữ liệu giả |
| Gọi API lại nhận HTML | URL đang trỏ frontend/Surge, không phải Flask; bỏ `VITE_API_URL` khi local |
| Cấu hình `.env` đã sửa nhưng vẫn dùng DB cũ | Restart backend; kiểm tra biến môi trường terminal có đang ghi đè `.env` không |
| Vite đổi port / port bị chiếm | Dừng phiên dev cũ hoặc giữ đúng 5173; nếu chủ động đổi port phải sửa CORS/FRONTEND_URL |
| Đăng nhập admin hiển thị Hà Linh | Đó là tên hồ sơ admin seed; kiểm tra username/role, dùng mật khẩu file local |
| `seed` báo đã có dữ liệu | Hành vi an toàn: không reset/ghi đè. Muốn bộ mẫu mới hãy dùng DB demo mới |
| Pytest không có LocalDB | Cài LocalDB hoặc đặt chuỗi tới DB test Express riêng `MayDrinksTest_*` |
| Món Trà dâu tươi bị 409 | Seed thiếu Siro dâu có chủ đích; demo nhập kho hoặc tạm hết món |

## 9. Quy tắc nghiệp vụ và phạm vi bản nộp

- Giá = giá món + phụ thu size/đường/đá/topping, backend tính lại khi đặt.
- Đơn chờ **chưa giữ chỗ tồn**; kiểm tra nguyên liệu khi đặt và khi nhận pha.
- Trừ nguyên liệu tại `pending → preparing` cùng transaction với trạng thái/lịch sử.
- Chỉ khách sở hữu được hủy khi `pending` và chưa đủ 60 giây kể từ lúc tạo đơn. Hết 60 giây hoặc đã nhận pha thì khóa hủy; staff/admin không có quyền hủy. Backend kiểm tra thời hạn, tải lại trang không đặt lại đồng hồ.
- Doanh thu chỉ ghi nhận đơn **completed + COD paid**; báo cáo dùng ranh giới ngày **UTC**.
- Không thanh toán ngân hàng thật, bản đồ, giao hàng real-time hoặc SLA 24/7.
- JSON đơn lưu snapshot lịch sử có chủ đích; bảng quan hệ SQL Server vẫn là nguồn dữ liệu chính.

Source nộp giữ: frontend, backend runtime, migrations, seed, test, ảnh/font đang dùng,
lockfile, cấu hình mẫu và tài liệu gốc. Không đưa `.venv`, `node_modules`, `dist`,
cache, backup cá nhân, mật khẩu, outbox hoặc DB runtime lên GitHub.
Dockerfile được giữ như lựa chọn cho giai đoạn hosting sau; không cần Docker để chạy Windows.
Các file Python runtime/Alembic/seed/test cần thiết **không được xóa** để làm gọn giả tạo.

Cloud AWS, Docker Linux, email Internet và nghiệm thu end-to-end public **chưa thực hiện**.
Khảo sát thực địa, thông tin nhóm, phê duyệt giả định và báo cáo học phần cần nhóm tự bổ sung;
không coi test local là bằng chứng đã hoàn tất các hạng mục này.
