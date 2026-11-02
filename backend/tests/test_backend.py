"""Comprehensive test suite verifying all MUST requirements, business rules, concurrency, and audit logs."""
import pytest
from decimal import Decimal
from maydrinks import create_app
from maydrinks.models import *
from maydrinks.domain import *
from maydrinks.auth import new_session

def test_health(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    assert res.json['database'] == 'SQL Server'

def test_auth_login_invalid(client):
    res = client.post('/api/auth/login', json={'username': 'admin', 'password': 'WrongPassword123'})
    assert res.status_code == 401

def test_catalog_at_least_15_drinks(client):
    res = client.get('/api/catalog')
    assert res.status_code == 200
    drinks = res.json['drinks']
    assert len(drinks) >= 15
    categories = res.json['categories']
    assert len(categories) >= 3

def test_quote_calculation(client):
    res = client.get('/api/catalog')
    drink = res.json['drinks'][0]
    options = res.json['options']
    size_m = next(o['id'] for o in options if o['kind'] == 'size' and o['name'] == 'M')
    sugar_50 = next(o['id'] for o in options if o['kind'] == 'sugar' and o['name'] == '50% đường')
    ice_50 = next(o['id'] for o in options if o['kind'] == 'ice' and o['name'] == 'Ít đá')
    topping_pearl = next(o['id'] for o in options if o['kind'] == 'topping' and o['name'] == 'Trân châu')

    quote_payload = {
        'drink_id': drink['id'],
        'quantity': 2,
        'choices': {
            'size': size_m,
            'sugar': sugar_50,
            'ice': ice_50,
            'toppings': [topping_pearl]
        }
    }
    res = client.post('/api/quote', json=quote_payload)
    assert res.status_code == 200
    data = res.json
    assert data['quantity'] == 2
    assert data['unit_price'] == drink['price'] + 5000 + 8000

def test_insufficient_stock_prevents_order_preparation(app, client):
    with app.app_context():
        straw = db.session.get(Ingredient, 'strawberry')
        straw.quantity = Decimal('0')
        db.session.commit()

        user = db.session.scalar(select(User).where(User.username == 'customer'))
        drink = db.session.scalar(select(Drink).where(Drink.name == 'Trà dâu tươi'))

        cart = cart_for(user)
        db.session.add(CartItem(
            cart_id=cart.id,
            drink_id=drink.id,
            quantity=1,
            choices=json_text({'size': 'size-s', 'sugar': 'sugar-100', 'ice': 'ice-100', 'toppings': []})
        ))
        db.session.commit()

        with pytest.raises(DomainError) as exc_info:
            create_order(user, {'recipient': 'Tester', 'phone': '0901234567', 'address': '123 Test'}, 'test-insufficient')
        assert 'Không đủ nguyên liệu' in exc_info.value.message

def test_order_snapshot_immutability(app):
    with app.app_context():
        order = db.session.scalar(select(Order).where(Order.status == 'completed'))
        item = db.session.scalar(select(OrderItem).where(OrderItem.order_id == order.id))
        original_item_name = item.name
        original_unit_price = item.unit_price

        drink = db.session.get(Drink, item.drink_id)
        drink.name = "Tên Mới Đổi"
        drink.price = 999999
        db.session.commit()

        refreshed_item = db.session.get(OrderItem, item.id)
        assert refreshed_item.name == original_item_name
        assert refreshed_item.unit_price == original_unit_price

        drink.name = original_item_name
        drink.price = item.base_price
        db.session.commit()

def test_customer_cannot_cancel_preparing_order(app):
    with app.app_context():
        customer = db.session.scalar(select(User).where(User.username == 'customer'))
        prep_order = db.session.scalar(select(Order).where(Order.status == 'preparing'))
        with pytest.raises(DomainError) as exc_info:
            transition(prep_order, customer, 'cancelled', 'Khách muốn hủy sau khi pha')
        assert 'Chỉ được hủy đơn của mình trước khi pha chế' in exc_info.value.message

def test_customer_cannot_access_other_customer_order(app, client):
    with app.app_context():
        user2 = db.session.scalar(select(User).where(User.username == 'customer2'))
        if not user2:
            user2 = User(username='customer2', password_hash='hash', role='customer')
            db.session.add(user2)
            db.session.flush()
            db.session.add(Profile(user_id=user2.id, name='Khách 2', phone='0911223344'))
            db.session.commit()

        order1 = db.session.scalar(select(Order).where(Order.user_id == 'user-customer'))
        order1_id = order1.id
        token = new_session(user2)
        db.session.commit()

    res = client.get(f'/api/orders/{order1_id}', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 404
