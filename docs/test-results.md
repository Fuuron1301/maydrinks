# Kết quả kiểm thử — 03/11/2026

**63 Pass · 0 Fail · 0 Skip · Microsoft SQL Server LocalDB · Alembic head**

Bộ test được gộp còn 2 module, bỏ các test trùng và bổ sung tình huống lỗi/API.
Số lượng case gồm các nhánh tham số hóa; không đánh đồng với số use case.

## Môi trường và tái lập

- Windows; Python 3.13.3; Node.js 24.18.0; ODBC Driver 18; SQL Server LocalDB.
- Mỗi lần chạy tự tạo database `MayDrinksTest_<random>`, áp dụng Alembic revision `fc2a96045963`.
- Reset seed từng test; không sửa database demo `MayDrinks`; xóa DB test tự tạo sau suite.
- Hash nhẹ chỉ ở test fixture. Runtime vẫn dùng Werkzeug scrypt.
- Kết quả lấy từ JUnit XML cục bộ; thời gian có thể khác giữa các máy.

```powershell
$env:PYTHONPATH='backend'
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q --junitxml=backend/instance/test-results.xml
npm run lint
npm run build
```

## Danh sách case thực tế

| Test case | File | Kết quả | Giây |
|---|---|---|---|
| `test_admin_menu_crud_keeps_historical_snapshot` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.957 |
| `test_ingredient_in_use_cannot_be_hidden[patch]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.288 |
| `test_ingredient_in_use_cannot_be_hidden[delete]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.295 |
| `test_recipe_hide_restore_and_duplicate_variant` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.335 |
| `test_receipt_confirm_once_and_immutable` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.328 |
| `test_receipt_failure_rolls_back_every_line` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.284 |
| `test_cancel_stock_policy_before_and_after_preparing[False]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.330 |
| `test_cancel_stock_policy_before_and_after_preparing[True]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.321 |
| `test_exact_stock_boundary_and_stale_status_do_not_double_deduct` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.305 |
| `test_concurrent_preparation_last_cup_only_one_succeeds` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.302 |
| `test_order_request_recovery_scoped_to_owner` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.312 |
| `test_role_matrix_denies_admin_mutations[/admin/recipes-customer]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.277 |
| `test_role_matrix_denies_admin_mutations[/admin/recipes-staff]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.262 |
| `test_role_matrix_denies_admin_mutations[/admin/ingredients-customer]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.271 |
| `test_role_matrix_denies_admin_mutations[/admin/ingredients-staff]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.275 |
| `test_role_matrix_denies_admin_mutations[/admin/drinks-customer]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.267 |
| `test_role_matrix_denies_admin_mutations[/admin/drinks-staff]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.270 |
| `test_role_matrix_denies_admin_mutations[/admin/users-customer]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.272 |
| `test_role_matrix_denies_admin_mutations[/admin/users-staff]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.273 |
| `test_malformed_quote_is_client_error_not_server_error[body0]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.253 |
| `test_malformed_quote_is_client_error_not_server_error[body1]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.264 |
| `test_malformed_quote_is_client_error_not_server_error[body2]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.266 |
| `test_malformed_quote_is_client_error_not_server_error[body3]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.275 |
| `test_malformed_quote_is_client_error_not_server_error[body4]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.252 |
| `test_malformed_admin_rows_are_rejected[/admin/receipts-body0]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.262 |
| `test_malformed_admin_rows_are_rejected[/admin/recipes-body1]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.280 |
| `test_malformed_admin_rows_are_rejected[/admin/drinks/M005-body2]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.267 |
| `test_malformed_admin_rows_are_rejected[/admin/options/top-pearl-body3]` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.259 |
| `test_low_stock_alert_aggregates_duplicate_ingredient_lines` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.701 |
| `test_login_logout_hash_and_session_revocation` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.294 |
| `test_disabled_topping_cannot_be_added_and_old_orders_still_readable` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.305 |
| `test_invalid_recipe_unit_rolls_back` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.283 |
| `test_password_reset_single_use_and_revokes_sessions` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.585 |
| `test_change_password_revokes_all_sessions` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.387 |
| `test_recipe_scaling_and_topping_unit_conversion` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.275 |
| `test_coupon_and_cod_revenue_recognition` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.405 |
| `test_registration_ignores_privilege_escalation` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.530 |
| `test_health_and_seed_acceptance_minimums` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.268 |
| `test_catalog_search_and_category_filter` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.276 |
| `test_cart_add_quantity_update_remove_and_foreign_cart` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.320 |
| `test_insufficient_stock_creation_is_atomic` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.346 |
| `test_customer_cannot_read_another_customer_order` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.277 |
| `test_state_machine_rejects_skips_and_malformed_status` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.322 |
| `test_admin_master_data_create_update_hide_restore` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.339 |
| `test_quote_all_surcharges_and_server_totals` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.278 |
| `test_delivery_complete_then_collect_cod_and_report_metrics` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.394 |
| `test_receipt_draft_creation_and_edit_do_not_change_stock` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.297 |
| `test_stock_alert_and_report_access_contracts` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.544 |
| `test_order_value_limit_returns_client_error_without_writing` | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.382 |
| `test_surge_origin_allowed` | [test_configuration.py](../backend/tests/test_configuration.py) | Pass | 0.015 |
| `test_readiness_does_not_query_database` | [test_configuration.py](../backend/tests/test_configuration.py) | Pass | 0.015 |
| `test_unknown_origin_rejected` | [test_configuration.py](../backend/tests/test_configuration.py) | Pass | 0.020 |
| `test_production_requires_remote_sqlserver` | [test_configuration.py](../backend/tests/test_configuration.py) | Pass | 0.001 |
| `test_production_requires_brevo_credentials` | [test_configuration.py](../backend/tests/test_configuration.py) | Pass | 0.001 |
| `test_brevo_reset_sent_over_https` | [test_configuration.py](../backend/tests/test_configuration.py) | Pass | 0.015 |
| `test_brevo_mail_error_does_not_expose_token` | [test_configuration.py](../backend/tests/test_configuration.py) | Pass | 0.016 |
| `test_local_database_settings_shared_with_app` | [test_configuration.py](../backend/tests/test_configuration.py) | Pass | 0.015 |
| `test_full_connection_string_takes_precedence` | [test_configuration.py](../backend/tests/test_configuration.py) | Pass | 0.001 |
| `test_invalid_local_sql_settings_rejected[SQLSERVER_SERVER-localhost;DATABASE=unexpected]` | [test_configuration.py](../backend/tests/test_configuration.py) | Pass | 0.001 |
| `test_invalid_local_sql_settings_rejected[SQLSERVER_DATABASE-MayDrinks;DROP DATABASE master]` | [test_configuration.py](../backend/tests/test_configuration.py) | Pass | 0.001 |
| `test_init_db_does_not_create_unintended_remote_database` | [test_configuration.py](../backend/tests/test_configuration.py) | Pass | 0.004 |
| `test_check_command_reads_current_sql_schema` | [test_configuration.py](../backend/tests/test_configuration.py) | Pass | 0.278 |
| `test_seed_again_preserves_existing_demo_records` | [test_configuration.py](../backend/tests/test_configuration.py) | Pass | 3.378 |

## Kiểm tra bổ sung ngoài pytest

- `manage.py check`: kết nối SQL thực, schema ở head, đọc số bản ghi.
- Quy trình README chạy từ bản sao backend sạch với DB mới: init-db → Alembic → seed → check: **Pass**.
- DB mới có 16 đồ uống, 15 nguyên liệu, 6 đơn; đăng nhập 3 vai trò bằng mật khẩu vừa sinh: **Pass**.
- Chạy seed lần hai không thay dữ liệu/mật khẩu; không ghi đè file tài khoản demo đang dùng: **Pass**.
- Alembic `check`: không phát hiện schema lệch model. Xuất DDL `upgrade head --sql`: **Pass**.
- `pip check`: không có dependency hỏng. Frontend lint và production build: **Pass**.
- API port 8000 và proxy Vite port 5173 `/api/health` đều trả JSON xác nhận SQL Server.
- Chrome DOM: coupon PATCH; khóa role chính admin; công thức ngừng/khôi phục; khóa loại tùy chọn đang sửa;
  cảnh báo món nguy cơ hết; nút tải lại đơn; chặn admin dùng giỏ khách.
- Menu 390px: không tràn ngang, một h1, không có alert lỗi. Đây không thay cho đánh giá thị giác đầy đủ.

## Giới hạn bằng chứng

- SQL Server và dữ liệu nghiệp vụ trong test là thật; nhà cung cấp email HTTPS được mock, không chứng minh delivery Internet.
- Mail local ghi `.eml`; có thể demo offline theo README. Không đưa token/thư thật lên Git.
- Chưa nghiệm thu Docker Linux, SQL/API trên AWS, frontend public end-to-end hoặc email gửi thật.
- Không khẳng định SLA 24/7, đo tải lớn, khảo sát thực địa hay phê duyệt SRS.
