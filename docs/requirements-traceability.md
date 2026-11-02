# Ma trận truy vết yêu cầu (RTM)

Nguồn: `2611COMP104406_Yeu-cau_NHOM2.pdf`, `ERD C3.docx`, `uc.docx` do chủ dự án cung cấp.
Bản PDF cho phép tên bảng/cột trong code khác sơ đồ, với điều kiện chứng minh đủ dữ liệu/rule.
Tham khảo bản chụp yêu cầu và sơ đồ ở [reference](./reference/).

## Kết quả kiểm tra ngày 03/11/2026

- Backend: **63 test cases Pass, 0 Fail**, chạy trên Microsoft SQL Server LocalDB riêng.
- Schema được tạo bằng Alembic, không thay SQL Server bằng SQLite.
- Dữ liệu seed được reset cho mỗi test; không chạy trên database demo đang dùng.
- Frontend: lint và production build Pass.
- `Pass` trong bảng dưới là bằng chứng **local**, không có nghĩa đã nghiệm thu cloud.
- Public API/SQL cloud và email Internet: **Deferred** theo kế hoạch chủ dự án; AWS cấu hình ở giai đoạn sau.
- Danh sách từng test và thời gian chạy nằm trong [test-results](./test-results.md).

| Yêu cầu | Mức | UI / API | Bằng chứng kiểm thử | Local |
|---|---|---|---|---|
| G2-FR01 đăng ký/đăng nhập, 3 vai trò | MUST | Đăng ký, đăng nhập, tài khoản; `/auth/*`, `/admin/users/<id>` | `test_registration_ignores_privilege_escalation`, `test_login_logout_hash_and_session_revocation`, `test_role_matrix_denies_admin_mutations`, `test_password_reset_single_use_and_revokes_sessions` | Pass |
| G2-FR02 quản lý đồ uống/danh mục/giá/ảnh/trạng thái | MUST | Quản trị → Thực đơn; `/admin/categories`, `/admin/drinks` | `test_admin_menu_crud_keeps_historical_snapshot`, `test_admin_master_data_create_update_hide_restore`, `test_health_and_seed_acceptance_minimums` | Pass |
| G2-FR03 size/topping/đá/đường và phụ thu | MUST | Tùy chọn; chi tiết món; `/admin/options`, `/quote` | `test_quote_all_surcharges_and_server_totals`, `test_recipe_scaling_and_topping_unit_conversion` | Pass |
| G2-FR04 tìm/xem menu, giỏ tùy chỉnh và số lượng | MUST | Thực đơn → Chi tiết → Giỏ; `/catalog`, `/cart/items` | `test_catalog_search_and_category_filter`, `test_cart_add_quantity_update_remove_and_foreign_cart`, `test_disabled_topping_cannot_be_added_and_old_orders_still_readable`, `test_malformed_quote_is_client_error_not_server_error` | Pass |
| G2-FR05 tạo đơn/tổng tiền/cấu hình snapshot | MUST | Checkout COD; `POST /orders`, `GET /orders/request/<key>` | `test_order_request_recovery_scoped_to_owner` (gồm gửi lại cùng khóa), `test_admin_menu_crud_keeps_historical_snapshot`, `test_coupon_and_cod_revenue_recognition`, `test_order_value_limit_returns_client_error_without_writing` | Pass |
| G2-FR06 luồng trạng thái và lịch sử/hủy | MUST | Đơn của tôi; khu vực nhân viên/quản trị; `/orders/<id>/status`, `/cancel` | `test_state_machine_rejects_skips_and_malformed_status`, `test_delivery_complete_then_collect_cod_and_report_metrics`, `test_cancel_stock_policy_before_and_after_preparing`, `test_exact_stock_boundary_and_stale_status_do_not_double_deduct` | Pass |
| G2-FR07 nguyên liệu và phiếu nhập/tăng tồn | MUST | Nguyên liệu, Phiếu nhập; `/admin/ingredients`, `/admin/receipts` | `test_receipt_draft_creation_and_edit_do_not_change_stock`, `test_receipt_confirm_once_and_immutable`, `test_receipt_failure_rolls_back_every_line`, `test_admin_master_data_create_update_hide_restore` | Pass |
| G2-FR08 công thức và mốc trừ nguyên liệu | MUST | Công thức món+size; `/admin/recipes`; bắt đầu pha chế | `test_recipe_hide_restore_and_duplicate_variant`, `test_recipe_scaling_and_topping_unit_conversion`, `test_exact_stock_boundary_and_stale_status_do_not_double_deduct` | Pass |
| G2-FR09 thiếu nguyên liệu phải chặn xác nhận | MUST | Checkout và thao tác nhận pha; thông báo thiếu cụ thể | `test_insufficient_stock_creation_is_atomic`, `test_concurrent_preparation_last_cup_only_one_succeeds`, `test_exact_stock_boundary_and_stale_status_do_not_double_deduct` | Pass |
| G2-FR10 dưới ngưỡng và món nguy cơ tạm hết | SHOULD | Tổng quan → Cảnh báo tồn/Món nguy cơ hết; `/admin/alerts` | `test_stock_alert_and_report_access_contracts`, `test_low_stock_alert_aggregates_duplicate_ingredient_lines` | Pass |
| G2-FR11 doanh thu/số đơn/bán chạy/tiêu hao | SHOULD | Báo cáo theo khoảng ngày; `/admin/reports` | `test_delivery_complete_then_collect_cod_and_report_metrics`, `test_coupon_and_cod_revenue_recognition`, `test_stock_alert_and_report_access_contracts` | Pass |
| G2-FR12 ưu đãi/tích điểm/đề xuất | COULD | Mã ưu đãi; coupon checkout | `test_coupon_and_cod_revenue_recognition` | Pass cho coupon; không triển khai tích điểm/đề xuất |

## Ánh xạ Use Case

| UC gốc | Hiện thực | Kiểm tra chính |
|---|---|---|
| USC01 đăng ký | Kiểm tra tên/điện thoại/mật khẩu, hash, role khách mặc định | FR01, đăng ký trùng bị 409 |
| USC02 xác thực/đăng xuất/quên/đổi mật khẩu | Session hash thu hồi được, token reset 15 phút dùng một lần | FR01; outbox `.eml` cho local, provider HTTPS được mock, delivery Internet hoãn |
| USC03 quản lý thực đơn/tùy chọn | Thêm/sửa/ẩn danh mục, món, cấu hình 4 loại tùy chọn | FR02/03; ẩn là xóa mềm để giữ lịch sử |
| USC04 xem/tìm/tùy chỉnh | Lọc theo tên/danh mục, quote từ backend | FR03/04 |
| USC05 quản lý giỏ | Thêm/xóa/sửa số lượng, tổng server | FR04 |
| USC06 đặt/hủy đơn và thanh toán | Idempotency, kiểm tra kho, snapshot, COD | FR05/06/09 |
| USC07 nhân viên xử lý | Kiểm tra lại kho, trừ một lần khi nhận pha, cập nhật đúng thứ tự | FR06/08/09 |
| USC08 đơn của chính khách | Danh sách/chi tiết/timeline; chống xem đơn người khác | `test_customer_cannot_read_another_customer_order` |
| USC09 nguyên liệu/công thức/nhập kho | CRUD mềm, đổi đơn vị hợp lệ, phiếu nháp/xác nhận một lần | FR07/08 |
| USC10 cảnh báo/báo cáo | Dưới ngưỡng, món <5 ly, doanh thu và tiêu hao | FR10/11 |

## Business rules đã chốt (giả định vận hành)

1. Giá = giá cơ bản + phụ thu size + đường + đá + tối đa 3 topping khác nhau.
2. Kiểm tra kho khi đặt đơn **và** khi nhân viên bắt đầu pha. Đơn chờ chưa giữ chỗ kho.
3. Chỉ trừ nguyên liệu ở `pending → preparing`, trong cùng transaction với trạng thái và audit.
4. SQL Server `sp_getapplock` tuần tự hóa thao tác ghi, phù hợp quy mô demo nhỏ.
5. Hủy trước pha không trừ kho. Sau pha chỉ admin hủy có lý do; không hoàn nguyên liệu đã dùng.
6. Khách chỉ hủy đơn của mình khi `pending`; staff không hủy, không sửa menu/kho.
7. Không xóa cứng master data. Đơn cũ giữ tên/giá/ảnh/cấu hình/định lượng snapshot.
8. Doanh thu chỉ ghi khi **hoàn tất + đã thu COD**; ngày ghi nhận là thời điểm muộn hơn.
9. Không thu tiền thật, không cổng thanh toán, không giao hàng real-time theo giới hạn đề.
10. Cảnh báo món <5 ly là ước tính từng công thức, chưa gồm topping/giữ kho đơn chờ.

## Phần không được coi là đã nghiệm thu

- Nghiệm thu end-to-end từ frontend public qua API cloud và SQL Server trên AWS (hoãn theo yêu cầu).
- Docker image thực tế trên Linux (daemon local chưa hoạt động).
- Brevo transactional email tới hộp thư thật, verified sender và quota.
- Khảo sát thực địa, phê duyệt giả định/Change Request bởi giảng viên.
- Đo tải nhiều người dùng hoặc SLA 24/7. Bản local chỉ chạy khi backend và SQL Server đang mở.

Không gọi toàn bộ bài nộp “100% hoàn thành” chỉ dựa vào test local.
