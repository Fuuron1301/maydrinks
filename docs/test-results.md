# K?t qu? ki?m th? ? 03/11/2026

**72 Pass ? 0 Fail ? SQL Server LocalDB ri?ng ? Alembic head**

L?nh: `python -m pytest backend/tests -q --junitxml=backend/instance/test-results.xml`

Kh?ng ch?y tr?n database demo/production. Mail provider ???c mock; kh?ng t?nh l? delivery th?t.

| Test case | File | K?t qu? | Gi?y |
|---|---|---|---|
| test_admin_menu_crud_keeps_historical_snapshot | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.928 |
| test_ingredient_in_use_cannot_be_hidden[patch] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.303 |
| test_ingredient_in_use_cannot_be_hidden[delete] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.283 |
| test_recipe_hide_restore_and_duplicate_variant | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.323 |
| test_receipt_confirm_once_and_immutable | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.344 |
| test_receipt_failure_rolls_back_every_line | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.357 |
| test_cancel_stock_policy_before_and_after_preparing[False] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.342 |
| test_cancel_stock_policy_before_and_after_preparing[True] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.335 |
| test_exact_stock_boundary_and_stale_status_do_not_double_deduct | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.320 |
| test_concurrent_preparation_last_cup_only_one_succeeds | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.352 |
| test_order_request_recovery_scoped_to_owner | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.314 |
| test_role_matrix_denies_admin_mutations[/admin/recipes-customer] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.266 |
| test_role_matrix_denies_admin_mutations[/admin/recipes-staff] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.294 |
| test_role_matrix_denies_admin_mutations[/admin/ingredients-customer] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.282 |
| test_role_matrix_denies_admin_mutations[/admin/ingredients-staff] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.304 |
| test_role_matrix_denies_admin_mutations[/admin/drinks-customer] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.267 |
| test_role_matrix_denies_admin_mutations[/admin/drinks-staff] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.267 |
| test_role_matrix_denies_admin_mutations[/admin/users-customer] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.292 |
| test_role_matrix_denies_admin_mutations[/admin/users-staff] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.265 |
| test_malformed_quote_is_client_error_not_server_error[body0] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.279 |
| test_malformed_quote_is_client_error_not_server_error[body1] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.284 |
| test_malformed_quote_is_client_error_not_server_error[body2] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.297 |
| test_malformed_quote_is_client_error_not_server_error[body3] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.297 |
| test_malformed_quote_is_client_error_not_server_error[body4] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.271 |
| test_malformed_admin_rows_are_rejected[/admin/receipts-body0] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.277 |
| test_malformed_admin_rows_are_rejected[/admin/recipes-body1] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.275 |
| test_malformed_admin_rows_are_rejected[/admin/drinks/M005-body2] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.267 |
| test_malformed_admin_rows_are_rejected[/admin/options/top-pearl-body3] | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.310 |
| test_low_stock_alert_aggregates_duplicate_ingredient_lines | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.549 |
| test_login_logout_hash_and_session_revocation | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.309 |
| test_disabled_topping_cannot_be_added_and_old_orders_still_readable | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.309 |
| test_invalid_recipe_unit_rolls_back | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.281 |
| test_password_reset_single_use_and_revokes_sessions | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.555 |
| test_change_password_revokes_all_sessions | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.551 |
| test_recipe_scaling_and_topping_unit_conversion | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.269 |
| test_coupon_and_cod_revenue_recognition | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.390 |
| test_registration_ignores_privilege_escalation | [test_acceptance.py](../backend/tests/test_acceptance.py) | Pass | 0.526 |
| test_health | [test_backend.py](../backend/tests/test_backend.py) | Pass | 0.267 |
| test_auth_login_invalid | [test_backend.py](../backend/tests/test_backend.py) | Pass | 0.276 |
| test_catalog_at_least_15_drinks | [test_backend.py](../backend/tests/test_backend.py) | Pass | 0.289 |
| test_quote_calculation | [test_backend.py](../backend/tests/test_backend.py) | Pass | 0.344 |
| test_insufficient_stock_prevents_order_preparation | [test_backend.py](../backend/tests/test_backend.py) | Pass | 0.295 |
| test_order_snapshot_immutability | [test_backend.py](../backend/tests/test_backend.py) | Pass | 0.294 |
| test_customer_cannot_cancel_preparing_order | [test_backend.py](../backend/tests/test_backend.py) | Pass | 0.328 |
| test_customer_cannot_access_other_customer_order | [test_backend.py](../backend/tests/test_backend.py) | Pass | 0.309 |
| test_surge_origin_allowed | [test_deployment.py](../backend/tests/test_deployment.py) | Pass | 0.022 |
| test_readiness_does_not_query_database | [test_deployment.py](../backend/tests/test_deployment.py) | Pass | 0.016 |
| test_unknown_origin_rejected | [test_deployment.py](../backend/tests/test_deployment.py) | Pass | 0.015 |
| test_production_requires_remote_sqlserver | [test_deployment.py](../backend/tests/test_deployment.py) | Pass | 0.002 |
| test_production_requires_brevo_credentials | [test_deployment.py](../backend/tests/test_deployment.py) | Pass | 0.001 |
| test_brevo_reset_sent_over_https | [test_deployment.py](../backend/tests/test_deployment.py) | Pass | 0.023 |
| test_brevo_mail_error_does_not_expose_token | [test_deployment.py](../backend/tests/test_deployment.py) | Pass | 0.016 |
| test_01_health_check | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.257 |
| test_02_register_customer | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.392 |
| test_03_login_wrong_credentials | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.259 |
| test_04_customer_cannot_access_admin_api | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.269 |
| test_05_admin_can_access_admin_api | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.266 |
| test_06_catalog_count_and_content | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.290 |
| test_07_pricing_formula_base_plus_size_and_topping | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.316 |
| test_08_cart_management | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.332 |
| test_09_create_order_idempotency | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.324 |
| test_10_insufficient_stock_prevents_order_creation | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.306 |
| test_11_order_state_transitions_correct_sequence | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.303 |
| test_12_customer_cancel_allowed_only_at_pending | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.294 |
| test_13_inventory_adjustment_creates_audit_transaction | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.311 |
| test_14_inventory_never_negative | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.265 |
| test_15_receipt_confirmation_increases_stock_once | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.522 |
| test_16_payment_cod_collected | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.285 |
| test_17_reports_endpoint | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.290 |
| test_18_stock_alerts_endpoint | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.552 |
| test_19_coupon_discount_calculation | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 0.266 |
| test_20_snapshot_immutability | [test_full_suite.py](../backend/tests/test_full_suite.py) | Pass | 3.422 |

## Ki?m tra frontend local

- `npm run lint`: Pass.
- `npm run build`: Pass.
- Chrome DOM: coupon PATCH, kh?a role ch?nh admin, c?ng th?c ng?ng/kh?i ph?c, kh?a lo?i t?y ch?n khi s?a, c?nh b?o m?n, n?t t?i l?i danh s?ch/chi ti?t ??n v? ch?n admin d?ng gi? kh?ch.
- Menu 390px: viewport=390, scrollWidth=390, m?t h1, kh?ng c? alert l?i. Ch?a thay cho ??nh gi? th? gi?c ??y ??.

## Gi?i h?n nghi?m thu

- Docker Linux, API/SQL production, Surge end-to-end, email th?t: ch?a nghi?m thu.
- Kh?ng x?c nh?n SLA 24/7, kh?o s?t th?c ??a hay ph? duy?t SRS.
