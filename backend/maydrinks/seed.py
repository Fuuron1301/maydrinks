"""Repeatable demonstration data, using the same business operations as the API."""
import os
import secrets
from pathlib import Path
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from flask import g, current_app
from sqlalchemy import select
from .models import *
from .domain import *


def seed():
    if db.session.scalar(select(User.id).limit(1)):
        return {'message':'Database already seeded; no existing data changed.'}
    credentials={}
    for role,name,number in [('admin','Hà Linh','0900000001'),('staff','Nhân viên pha chế','0900000002'),('customer','Nguyễn Minh Anh','0900000003')]:
        password=os.environ.get('DEMO_PASSWORD') or secrets.token_urlsafe(14)+'9a'
        user=User(id='user-'+role,username=role,password_hash=generate_password_hash(password),role=role)
        db.session.add(user); db.session.flush()
        db.session.add(Profile(user_id=user.id,name=name,phone=number,email=role+'@maydrinks.example',address='24 Nguyễn Huệ, TP. Hồ Chí Minh'))
        db.session.add(Cart(id='cart-'+role,user_id=user.id))
        credentials[role]={'username':role,'password':password}
    db.session.flush(); admin=get(User,'user-admin'); g.user=admin
    cats=['Trà trái cây','Cà phê','Trà sữa','Matcha','Đá xay']
    for index,name in enumerate(cats): db.session.add(Category(id='cat-'+str(index),name=name))
    options=[('size-s','size','S',0,1),('size-m','size','M',5000,1),('size-l','size','L',11000,1),('sugar-0','sugar','Không đường',0,0),('sugar-30','sugar','30% đường',0,.3),('sugar-50','sugar','50% đường',0,.5),('sugar-100','sugar','Đường bình thường',0,1),('ice-0','ice','Không đá',0,0),('ice-50','ice','Ít đá',0,.5),('ice-100','ice','Đá bình thường',0,1),('top-pearl','topping','Trân châu',8000,1),('top-peach','topping','Thạch đào',8000,1),('top-cheese','topping','Kem cheese',10000,1)]
    for key,kind,name,price,factor in options: db.session.add(Option(id=key,kind=kind,name=name,surcharge=price,factor=factor))
    stocks=[('coffee','Cà phê hạt','kg',5,2,185000),('jasmine','Trà lài','kg',2,.5,220000),('milk','Sữa tươi','l',8,10,32000),('peach','Siro đào','l',1.2,2,95000),('blacktea','Trà đen','kg',.45,.5,180000),('fruit','Đào ngâm','kg',5,2,95000),('orange','Cam tươi','kg',5,3,35000),('lemongrass','Sả tươi','kg',2,.5,25000),('sugar','Siro đường','l',10,2,25000),('matcha','Bột matcha','kg',3,.5,450000),('pearl','Trân châu','kg',5,1,65000),('jelly','Thạch đào','kg',5,1,75000),('cheese','Kem cheese','kg',4,1,120000),('ice','Đá viên','kg',50,10,3000),('strawberry','Siro dâu','l',0,.5,90000)]
    for key,name,unit,qty,minimum,price in stocks:
        ing=Ingredient(id=key,name=name,unit=unit,quantity=qty,minimum=minimum,last_price=price)
        db.session.add(ing)
    db.session.flush()
    for key,name,unit,qty,minimum,price in stocks:
        db.session.add(InventoryTransaction(ingredient_id=key,kind='opening',delta=qty,balance=qty,unit_cost=price,actor_id=admin.id,reason='Tồn đầu kỳ dữ liệu seed'))
    for key,ing in [('top-pearl','pearl'),('top-peach','jelly'),('top-cheese','cheese')]: db.session.add(ToppingLine(option_id=key,ingredient_id=ing,quantity=30,unit='g'))
    drinks=[('Trà đào cam sả',0,34000,'tea'),('Cà phê sữa đá',1,30000,'coffee_milk'),('Matcha latte',3,44000,'matcha_milk'),('Trà sữa trân châu',2,40000,'milk_tea'),('Cà phê đen đá',1,24000,'coffee'),('Trà sữa ô long',2,40000,'milk_tea'),('Matcha đá xay',4,50000,'matcha_milk'),('Trà cam thanh mát',0,34000,'orange_tea'),('Bạc xỉu',1,34000,'coffee_milk'),('Cà phê kem cheese',1,44000,'coffee_milk'),('Trà lài đào',0,30000,'tea'),('Trà đen cam',0,34000,'orange_tea'),('Trà sữa kem cheese',2,44000,'milk_tea'),('Matcha kem cheese',3,49000,'matcha_milk'),('Trà đào đá xay',4,44000,'tea'),('Trà dâu tươi',0,39000,'strawberry_tea')]
    recipe_base={'tea':[('jasmine',5,'g'),('peach',20,'ml'),('fruit',40,'g'),('orange',20,'g'),('lemongrass',8,'g')],'coffee':[('coffee',18,'g')],'coffee_milk':[('coffee',18,'g'),('milk',70,'ml')],'matcha_milk':[('matcha',4,'g'),('milk',140,'ml')],'milk_tea':[('blacktea',6,'g'),('milk',100,'ml')],'orange_tea':[('blacktea',5,'g'),('orange',70,'g')],'strawberry_tea':[('jasmine',5,'g'),('strawberry',30,'ml')]}
    for index,(name,cat,price,recipe_kind) in enumerate(drinks):
        drink=Drink(id=f'M{index+1:03}',category_id='cat-'+str(cat),name=name,price=price,image=f'/assets/product-{index%8}.jpg',description='Pha mới theo công thức của Mây, tùy chỉnh đường và đá theo gu của bạn.')
        db.session.add(drink); db.session.flush()
        for opt in options: db.session.add(DrinkOption(drink_id=drink.id,option_id=opt[0]))
        for size,factor in [('s',Decimal('1')),('m',Decimal('1.25')),('l',Decimal('1.6'))]:
            recipe=Recipe(id=f'recipe-{index+1}-{size}',drink_id=drink.id,size_id='size-'+size,name=name+' '+size.upper(),instructions='Ủ trà hoặc chiết xuất cà phê. Đong đúng định lượng, phối nguyên liệu, điều chỉnh đường và đá theo đơn. Kiểm tra trước khi phục vụ.')
            db.session.add(recipe); db.session.flush()
            for ing,qty,unit in recipe_base[recipe_kind]: db.session.add(RecipeLine(recipe_id=recipe.id,ingredient_id=ing,quantity=Decimal(qty)*factor,unit=unit))
            db.session.add(RecipeLine(recipe_id=recipe.id,ingredient_id='sugar',quantity=15*factor,unit='ml',scales_with='sugar'))
            db.session.add(RecipeLine(recipe_id=recipe.id,ingredient_id='ice',quantity=120*factor,unit='g',scales_with='ice'))
    db.session.add(Coupon(code='MAY10',percent=10,minimum=50000,expires_at=utcnow()+timedelta(days=365)))
    db.session.flush()
    customer=get(User,'user-customer'); cart=get(Cart,'cart-customer')
    for index,target in enumerate(['pending','preparing','ready','completed','cancelled']):
        g.user=customer
        raw={'size':'size-m','sugar':'sugar-50','ice':'ice-50','toppings':[]}
        db.session.add(CartItem(cart_id=cart.id,drink_id=f'M{index+1:03}',quantity=1,choices=json_text(raw))); db.session.flush()
        order=create_order(customer,{'recipient':'Nguyễn Minh Anh','phone':'0900000003','address':'24 Nguyễn Huệ, TP. Hồ Chí Minh','note':'Đơn mẫu cho kịch bản nghiệm thu.'},'seed-'+str(index))
        g.user=admin
        if target=='cancelled': transition(order,customer,target,'Khách thay đổi kế hoạch trước khi pha chế')
        else:
            for status in ['preparing','ready','completed']:
                if target=='pending': break
                transition(order,admin,status)
                if status==target: break
        order.created_at=utcnow()-timedelta(days=index%3)
        if target=='completed':
            payment=db.session.scalar(select(Payment).where(Payment.order_id==order.id)); payment.status='paid'; payment.actor_id=admin.id; payment.paid_at=utcnow(); order.completed_at=utcnow()
        db.session.flush()
    receipt=Receipt(id='receipt-demo',code='NK-DEMO-001',supplier='An Nhiên Food',received_date=date.today(),actor_id=admin.id,note='Phiếu nháp: chưa cộng vào tồn.')
    db.session.add(receipt); db.session.flush()
    for ing,qty,price in [('milk',20,32000),('peach',5,95000),('blacktea',2,180000)]: db.session.add(ReceiptLine(receipt_id=receipt.id,ingredient_id=ing,quantity=qty,price=price))
    db.session.commit()
    if not current_app.testing:
        path=Path(current_app.instance_path)/'demo-accounts.json'; path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json_text(credentials),encoding='utf-8')
    return {'message':'Seeded 16 drinks, 15 ingredients, 3 sizes, 3 toppings, 5 orders.','credentials':credentials}
