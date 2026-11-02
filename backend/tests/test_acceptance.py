"""Acceptance tests against real SQL Server; see docs/requirements-traceability.md."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select, func
from werkzeug.security import check_password_hash

from maydrinks.auth import new_session
from maydrinks.domain import cart_for, create_order, json_text, inventory_needs, order_items
from maydrinks.models import *

CHOICES = {'size': 'size-s', 'sugar': 'sugar-100', 'ice': 'ice-100', 'toppings': []}
DELIVERY = {'recipient': 'Khách kiểm thử', 'phone': '0901234567', 'address': '24 Nguyễn Huệ'}


def headers(app, role='admin'):
    with app.app_context():
        token = new_session(db.session.get(User, 'user-' + role))
        db.session.commit()
    return {'Authorization': 'Bearer ' + token}


def new_order(app, drink_id='M005', quantity=1):
    with app.app_context():
        user = db.session.get(User, 'user-customer')
        cart = cart_for(user)
        db.session.add(CartItem(cart_id=cart.id, drink_id=drink_id, quantity=quantity, choices=json_text(CHOICES)))
        db.session.flush()
        order = create_order(user, DELIVERY, str(uuid4()))
        db.session.commit()
        return order.id


def state(client, auth, order_id, before, after):
    return client.post('/api/orders/' + order_id + '/status', headers=auth,
                       json={'expected_status': before, 'status': after})


def test_admin_menu_crud_keeps_historical_snapshot(app, client):
    auth = headers(app)
    with app.app_context():
        item = db.session.scalar(select(OrderItem).where(OrderItem.drink_id == 'M005'))
        before = (item.name, item.unit_price, item.choices)
        item_id = item.id
    assert client.patch('/api/admin/drinks/M005', headers=auth, json={'name': 'Cà phê mới', 'price': 45000}).status_code == 200
    assert client.delete('/api/admin/drinks/M005', headers=auth).status_code == 200
    assert 'M005' not in [d['id'] for d in client.get('/api/catalog').json['drinks']]
    assert client.post('/api/quote', json={'drink_id': 'M005', 'choices': CHOICES}).status_code == 404
    with app.app_context():
        item = db.session.get(OrderItem, item_id)
        assert (item.name, item.unit_price, item.choices) == before


@pytest.mark.parametrize('method', ['patch', 'delete'])
def test_ingredient_in_use_cannot_be_hidden(app, client, method):
    auth = headers(app)
    response = getattr(client, method)('/api/admin/ingredients/coffee', headers=auth, json={'active': False})
    assert response.status_code == 409
    with app.app_context():
        assert db.session.get(Ingredient, 'coffee').active


def test_recipe_hide_restore_and_duplicate_variant(app, client):
    auth = headers(app)
    endpoint = '/api/admin/recipes/recipe-5-s'
    assert client.delete(endpoint, headers=auth).json['active'] is False
    assert client.post('/api/quote', json={'drink_id': 'M005', 'choices': CHOICES}).status_code == 409
    restored = client.patch(endpoint, headers=auth, json={'active': True})
    assert restored.status_code == 200 and restored.json['active']
    assert client.post('/api/quote', json={'drink_id': 'M005', 'choices': CHOICES}).status_code == 200
    duplicate = client.post('/api/admin/recipes', headers=auth, json={
        'drink_id': 'M005', 'size_id': 'size-s', 'name': 'Trùng biến thể',
        'lines': [{'ingredient_id': 'coffee', 'quantity': 18, 'unit': 'g'}],
    })
    assert duplicate.status_code == 409


def test_receipt_confirm_once_and_immutable(app, client):
    auth = headers(app)
    with app.app_context():
        before = db.session.get(Ingredient, 'milk').quantity
    endpoint = '/api/admin/receipts/receipt-demo'
    first = client.post(endpoint + '/confirm', headers=auth)
    second = client.post(endpoint + '/confirm', headers=auth)
    assert first.status_code == second.status_code == 200
    assert first.json['status'] == 'confirmed'
    assert client.patch(endpoint, headers=auth, json={'supplier': 'Không được sửa'}).status_code == 409
    with app.app_context():
        assert db.session.get(Ingredient, 'milk').quantity == before + Decimal('20')
        count = db.session.scalar(select(func.count()).select_from(InventoryTransaction).where(
            InventoryTransaction.receipt_id == 'receipt-demo', InventoryTransaction.ingredient_id == 'milk'))
        assert count == 1


def test_receipt_failure_rolls_back_every_line(app, client):
    auth = headers(app)
    with app.app_context():
        milk = db.session.get(Ingredient, 'milk').quantity
        db.session.get(Ingredient, 'peach').active = False
        db.session.commit()
    response = client.post('/api/admin/receipts/receipt-demo/confirm', headers=auth)
    assert response.status_code == 404
    with app.app_context():
        assert db.session.get(Ingredient, 'milk').quantity == milk
        assert db.session.get(Receipt, 'receipt-demo').status == 'draft'
        assert db.session.scalar(select(func.count()).select_from(InventoryTransaction).where(
            InventoryTransaction.receipt_id == 'receipt-demo')) == 0


@pytest.mark.parametrize('after_preparing', [False, True])
def test_cancel_stock_policy_before_and_after_preparing(app, client, after_preparing):
    order_id = new_order(app)
    admin, customer = headers(app), headers(app, 'customer')
    with app.app_context():
        before = db.session.get(Ingredient, 'coffee').quantity
    if after_preparing:
        assert state(client, admin, order_id, 'pending', 'preparing').status_code == 200
        assert client.post('/api/orders/' + order_id + '/cancel', headers=customer, json={'reason': 'Hủy'}).status_code == 403
    cancelled = client.post('/api/orders/' + order_id + '/cancel', headers=admin if after_preparing else customer,
                            json={'reason': 'Kiểm thử hủy'})
    assert cancelled.status_code == 200
    with app.app_context():
        assert db.session.get(Ingredient, 'coffee').quantity == before - (Decimal('.018') if after_preparing else 0)
        count = db.session.scalar(select(func.count()).select_from(InventoryTransaction).where(
            InventoryTransaction.order_id == order_id))
        assert count == (3 if after_preparing else 0)


def test_exact_stock_boundary_and_stale_status_do_not_double_deduct(app, client):
    order_id = new_order(app)
    auth = headers(app, 'staff')
    with app.app_context():
        needs = inventory_needs(order_items(db.session.get(Order, order_id)))
        for key, value in needs.items():
            db.session.get(Ingredient, key).quantity = value
        db.session.commit()
    assert state(client, auth, order_id, 'pending', 'preparing').status_code == 200
    assert state(client, auth, order_id, 'pending', 'preparing').status_code == 409
    with app.app_context():
        assert all(db.session.get(Ingredient, key).quantity == 0 for key in needs)
        assert db.session.scalar(select(func.count()).select_from(InventoryTransaction).where(
            InventoryTransaction.order_id == order_id)) == len(needs)


def test_concurrent_preparation_last_cup_only_one_succeeds(app):
    orders = [new_order(app), new_order(app)]
    auth = headers(app, 'staff')
    with app.app_context():
        db.session.get(Ingredient, 'coffee').quantity = Decimal('.018')
        db.session.commit()
    def prepare(order_id):
        with app.test_client() as client:
            return state(client, auth, order_id, 'pending', 'preparing').status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(prepare, orders))
    assert sorted(results) == [200, 409]
    with app.app_context():
        assert db.session.get(Ingredient, 'coffee').quantity == 0
        assert sum(db.session.get(Order, key).stock_deducted for key in orders) == 1


def test_order_request_recovery_scoped_to_owner(app, client):
    auth = headers(app, 'customer')
    assert client.post('/api/cart/items', headers=auth, json={'drink_id': 'M005', 'choices': CHOICES}).status_code == 201
    auth['Idempotency-Key'] = 'recovery-test'
    first = client.post('/api/orders', headers=auth, json=DELIVERY)
    assert first.status_code == 201
    assert client.post('/api/orders', headers=auth, json=DELIVERY).json['id'] == first.json['id']
    recovered = client.get('/api/orders/request/recovery-test', headers=auth)
    assert recovered.status_code == 200 and recovered.json['id'] == first.json['id']
    assert client.get('/api/orders/request/other-key', headers=auth).status_code == 404
    assert client.get('/api/orders/request/recovery-test', headers=headers(app, 'staff')).status_code == 403


@pytest.mark.parametrize('role', ['customer', 'staff'])
@pytest.mark.parametrize('path', ['/admin/recipes', '/admin/ingredients', '/admin/drinks', '/admin/users'])
def test_role_matrix_denies_admin_mutations(app, client, role, path):
    method = 'PATCH' if path == '/admin/users' else 'POST'
    endpoint = '/api' + path + ('/user-admin' if method == 'PATCH' else '')
    assert client.open(endpoint, method=method, headers=headers(app, role), json={}).status_code == 403


@pytest.mark.parametrize('body', [
    {'drink_id': []}, {'drink_id': 'M005', 'choices': []},
    {'drink_id': 'M005', 'choices': {**CHOICES, 'toppings': [{}]}},
    {'drink_id': 'M005', 'choices': {**CHOICES, 'size': {}}},
    {'drink_id': 'M005', 'choices': CHOICES, 'quantity': True},
])
def test_malformed_quote_is_client_error_not_server_error(client, body):
    assert client.post('/api/quote', json=body).status_code == 400


@pytest.mark.parametrize('endpoint,body', [
    ('/admin/receipts', {'supplier': 'X', 'received_date': '2026-11-02', 'lines': [7]}),
    ('/admin/recipes', {'drink_id': 'M005', 'size_id': 'size-s', 'name': 'Sai', 'lines': [7]}),
    ('/admin/drinks/M005', {'option_ids': [{}]}),
    ('/admin/options/top-pearl', {'ingredients': [7]}),
])
def test_malformed_admin_rows_are_rejected(app, client, endpoint, body):
    response = client.open('/api' + endpoint, method='PATCH' if endpoint.count('/') > 2 else 'POST',
                           headers=headers(app), json=body)
    assert response.status_code == 400


def test_low_stock_alert_aggregates_duplicate_ingredient_lines(app, client):
    with app.app_context():
        db.session.get(Ingredient, 'coffee').quantity = Decimal('.030')
        db.session.add(RecipeLine(recipe_id='recipe-5-s', ingredient_id='coffee', quantity=18, unit='g'))
        db.session.commit()
    result = client.get('/api/admin/alerts', headers=headers(app))
    assert result.status_code == 200
    entry = next(row for row in result.json['at_risk'] if row['drink_id'] == 'M005' and row['size'] == 'S')
    assert entry['cups'] == 0


def test_login_logout_hash_and_session_revocation(app, client):
    login = client.post('/api/auth/login', json={'username': 'admin', 'password': 'TestOnly12345'})
    assert login.status_code == 200 and login.json['user']['role'] == 'admin'
    token = {'Authorization': 'Bearer ' + login.json['token']}
    with app.app_context():
        user = db.session.get(User, 'user-admin')
        assert user.password_hash != 'TestOnly12345'
        assert check_password_hash(user.password_hash, 'TestOnly12345')
    assert client.post('/api/auth/logout', headers=token).status_code == 200
    assert client.get('/api/auth/me', headers=token).status_code == 401


def test_disabled_topping_cannot_be_added_and_old_orders_still_readable(app, client):
    admin, customer = headers(app), headers(app, 'customer')
    assert client.delete('/api/admin/options/top-pearl', headers=admin).status_code == 200
    result = client.post('/api/cart/items', headers=customer,
                         json={'drink_id': 'M005', 'choices': {**CHOICES, 'toppings': ['top-pearl']}})
    assert result.status_code == 404
    assert client.get('/api/orders', headers=customer).status_code == 200


def test_invalid_recipe_unit_rolls_back(app, client):
    auth = headers(app)
    result = client.patch('/api/admin/recipes/recipe-5-s', headers=auth, json={
        'lines': [{'ingredient_id': 'coffee', 'quantity': 18, 'unit': 'ml'}],
    })
    assert result.status_code == 400
    assert client.post('/api/quote', json={'drink_id': 'M005', 'choices': CHOICES}).status_code == 200


def test_password_reset_single_use_and_revokes_sessions(app, client, monkeypatch):
    auth = headers(app, 'customer')
    sent = []
    monkeypatch.setattr('maydrinks.auth.send_reset', lambda address, link: sent.append((address, link)))
    response = client.post('/api/auth/forgot-password', json={'email': 'customer@maydrinks.example'})
    assert response.status_code == 200 and 'token' not in response.json
    from urllib.parse import urlsplit, parse_qs
    token = parse_qs(urlsplit(sent[0][1]).query)['token'][0]
    assert client.post('/api/auth/reset-password', json={'token': token, 'password': 'ChangedPass123'}).status_code == 200
    assert client.get('/api/auth/me', headers=auth).status_code == 401
    assert client.post('/api/auth/reset-password', json={'token': token, 'password': 'ChangedAgain123'}).status_code == 400
    assert client.post('/api/auth/login', json={'username': 'customer', 'password': 'ChangedPass123'}).status_code == 200


def test_change_password_revokes_all_sessions(app, client):
    auth = headers(app, 'customer')
    other = headers(app, 'customer')
    assert client.post('/api/auth/change-password', headers=auth,
                       json={'current_password': 'Wrong123', 'password': 'ChangedPass123'}).status_code == 400
    assert client.post('/api/auth/change-password', headers=auth,
                       json={'current_password': 'TestOnly12345', 'password': 'ChangedPass123'}).status_code == 200
    assert client.get('/api/auth/me', headers=other).status_code == 401


def test_recipe_scaling_and_topping_unit_conversion(app):
    from maydrinks.domain import price_item
    with app.app_context():
        item = price_item({'drink_id': 'M005', 'choices': {
            'size': 'size-l', 'sugar': 'sugar-30', 'ice': 'ice-50', 'toppings': ['top-pearl'],
        }})
        assert Decimal(item['requirements']['coffee']) == Decimal('.0288')
        assert Decimal(item['requirements']['sugar']) == Decimal('.0072')
        assert Decimal(item['requirements']['ice']) == Decimal('.0960')
        assert Decimal(item['requirements']['pearl']) == Decimal('.0300')


def test_coupon_and_cod_revenue_recognition(app, client):
    customer, staff, admin = headers(app, 'customer'), headers(app, 'staff'), headers(app)
    assert client.post('/api/cart/items', headers=customer,
                       json={'drink_id': 'M005', 'quantity': 3, 'choices': CHOICES}).status_code == 201
    customer['Idempotency-Key'] = 'coupon-cod-test'
    created = client.post('/api/orders', headers=customer, json={**DELIVERY, 'coupon': 'MAY10'})
    assert created.status_code == 201
    order = created.json
    assert order['subtotal'] == 72000 and order['discount'] == 7200 and order['total'] == 64800
    before = client.get('/api/admin/reports', headers=admin).json['revenue']
    order_id = order['id']
    assert client.post('/api/orders/' + order_id + '/payment', headers=staff, json={'amount': 64800}).status_code == 409
    assert state(client, staff, order_id, 'pending', 'preparing').status_code == 200
    assert state(client, staff, order_id, 'preparing', 'ready').status_code == 200
    assert client.post('/api/orders/' + order_id + '/payment', headers=staff, json={'amount': 1}).status_code == 400
    assert client.post('/api/orders/' + order_id + '/payment', headers=staff, json={'amount': 64800}).status_code == 200
    assert client.get('/api/admin/reports', headers=admin).json['revenue'] == before
    assert state(client, staff, order_id, 'ready', 'completed').status_code == 200
    assert client.get('/api/admin/reports', headers=admin).json['revenue'] == before + 64800


def test_registration_ignores_privilege_escalation(app, client):
    response = client.post('/api/auth/register', json={
        'username': 'new_customer', 'password': 'SecurePass123', 'name': 'Khách mới',
        'phone': '0987654321', 'email': 'new@example.org', 'role': 'admin',
    })
    assert response.status_code == 201 and response.json['user']['role'] == 'customer'
    assert client.post('/api/auth/register', json={
        'username': 'new_customer', 'password': 'SecurePass123', 'name': 'Trùng', 'phone': '0987654322',
    }).status_code == 409
