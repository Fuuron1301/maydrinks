"""Opaque revocable sessions; password reset tokens are hashed and single-use."""
import hashlib
import secrets
import os
import smtplib
import json
import logging
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from email.message import EmailMessage
from pathlib import Path
from datetime import timedelta
from functools import wraps
from flask import Blueprint, request, g, jsonify, current_app
from sqlalchemy import select, delete, or_
from werkzeug.security import generate_password_hash, check_password_hash
from . import limiter
from .models import *
from .domain import *

auth=Blueprint('auth',__name__)
def digest(token): return hashlib.sha256(token.encode()).hexdigest()
def payload():
    data=request.get_json(silent=True)
    if not isinstance(data,dict): raise DomainError('Yêu cầu phải là JSON object.')
    return data

def require(*roles):
    def decorate(fn):
        @wraps(fn)
        def wrapped(*args,**kwargs):
            token=request.headers.get('Authorization','')
            if not token.startswith('Bearer '): raise DomainError('Vui lòng đăng nhập.',401)
            session=db.session.get(AuthSession,digest(token[7:]))
            if not session or session.expires_at<utcnow(): raise DomainError('Phiên đăng nhập đã hết hạn.',401)
            user=get(User,session.user_id)
            if not user.active: raise DomainError('Tài khoản đã bị vô hiệu hóa.',401)
            if roles and user.role not in roles: raise DomainError('Bạn không có quyền thực hiện thao tác này.',403)
            g.user=user; g.session=session
            return fn(*args,**kwargs)
        return wrapped
    return decorate

def password(value):
    if not isinstance(value,str) or not 8<=len(value)<=128 or not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
        raise DomainError('Mật khẩu cần 8–128 ký tự, gồm chữ và số.')
    return value

def new_session(user):
    token=secrets.token_urlsafe(48)
    db.session.add(AuthSession(token_hash=digest(token),user_id=user.id,expires_at=utcnow()+timedelta(hours=12)))
    return token

@auth.post('/register')
@limiter.limit('10 per hour')
def register():
    data=payload()
    username=text(data.get('username'),'Tên đăng nhập',80).lower()
    if not re.fullmatch(r'[a-z0-9_.-]{3,80}',username): raise DomainError('Tên đăng nhập gồm 3–80 chữ không dấu, số, dấu . _ -')
    user=User(username=username,password_hash=generate_password_hash(password(data.get('password'))),role='customer')
    db.session.add(user); db.session.flush()
    db.session.add(Profile(user_id=user.id,name=text(data.get('name'),'Họ tên'),phone=phone(data.get('phone')),email=email(data.get('email')),address=text(data.get('address',''),'Địa chỉ',500,False)))
    db.session.add(Cart(user_id=user.id)); db.session.flush()
    g.user=user; token=new_session(user); audit('auth.register',user.id)
    result=user_data(user); db.session.commit()
    return jsonify(user=result,token=token),201

@auth.post('/login')
@limiter.limit('15 per minute')
def login():
    data=payload(); identity=text(data.get('username'),'Tên đăng nhập',80).lower()
    user=db.session.scalar(select(User).join(Profile,Profile.user_id==User.id).where(or_(User.username==identity,Profile.phone==identity)))
    if not user or not check_password_hash(user.password_hash,str(data.get('password',''))) or not user.active:
        raise DomainError('Tài khoản hoặc mật khẩu không đúng.',401)
    g.user=user; token=new_session(user); audit('auth.login',user.id)
    result=user_data(user); db.session.commit()
    return jsonify(user=result,token=token)

@auth.get('/me')
@require()
def me(): return jsonify(user_data(g.user))

@auth.post('/logout')
@require()
def logout():
    db.session.delete(g.session); audit('auth.logout',g.user.id); db.session.commit()
    return jsonify(message='Đã đăng xuất.')

@auth.patch('/profile')
@require()
def profile():
    data=payload(); profile=get(Profile,g.user.id)
    for key,validator in [('name',lambda v:text(v,'Họ tên')),('phone',phone),('email',email),('address',lambda v:text(v,'Địa chỉ',500,False))]:
        if key in data: setattr(profile,key,validator(data[key]))
    audit('profile.updated',g.user.id); db.session.commit()
    return jsonify(user_data(g.user))

@auth.post('/change-password')
@require()
def change_password():
    data=payload()
    if not check_password_hash(g.user.password_hash,str(data.get('current_password',''))): raise DomainError('Mật khẩu hiện tại không đúng.')
    g.user.password_hash=generate_password_hash(password(data.get('password')))
    db.session.execute(delete(AuthSession).where(AuthSession.user_id==g.user.id))
    db.session.execute(delete(PasswordReset).where(PasswordReset.user_id==g.user.id))
    audit('auth.password_changed',g.user.id); db.session.commit()
    return jsonify(message='Đã đổi mật khẩu. Vui lòng đăng nhập lại.')

def send_reset(address,link):
    msg=EmailMessage(); msg['Subject']='Mây Drinks — Đặt lại mật khẩu'; msg['From']=os.environ.get('BREVO_SENDER_EMAIL') or os.environ.get('SMTP_FROM','no-reply@maydrinks.local'); msg['To']=address
    msg.set_content('Liên kết có hiệu lực 15 phút và chỉ dùng một lần:\n'+link+'\nNếu không yêu cầu, hãy bỏ qua email này.')
    mode=current_app.config['MAIL_MODE']
    if mode=='file':
        out=Path(current_app.instance_path)/'mail-outbox'; out.mkdir(parents=True,exist_ok=True)
        (out/(uid()+'.eml')).write_text(msg.as_string(),encoding='utf-8')
    elif mode=='brevo':
        body={'sender':{'name':'Mây Drinks','email':os.environ['BREVO_SENDER_EMAIL']},'to':[{'email':address}], 'subject':msg['Subject'], 'textContent':msg.get_content()}
        request=Request('https://api.brevo.com/v3/smtp/email',data=json.dumps(body,ensure_ascii=False).encode('utf-8'),headers={'api-key':os.environ['BREVO_API_KEY'],'Content-Type':'application/json'},method='POST')
        try:
            with urlopen(request,timeout=15) as response:
                if response.status!=201: raise RuntimeError('Brevo did not accept the reset email.')
        except (HTTPError,URLError,TimeoutError) as error:
            logging.getLogger(__name__).warning('Password reset email delivery failed: %s',type(error).__name__)
            raise DomainError('Không gửi được email khôi phục lúc này. Vui lòng thử lại sau.',503) from error
    elif mode=='smtp':
        with smtplib.SMTP(os.environ['SMTP_HOST'],int(os.environ.get('SMTP_PORT','587')),timeout=15) as smtp:
            smtp.starttls()
            if os.environ.get('SMTP_USER'): smtp.login(os.environ['SMTP_USER'],os.environ['SMTP_PASSWORD'])
            smtp.send_message(msg)
    else:
        raise RuntimeError('Mail delivery mode is not configured.')

@auth.post('/forgot-password')
@limiter.limit('5 per hour')
def forgot():
    data=payload(); address=email(data.get('email'))
    if not address: raise DomainError('Vui lòng nhập email.')
    profile=db.session.scalar(select(Profile).where(Profile.email==address))
    if profile:
        user=get(User,profile.user_id)
        if user.active:
            db.session.execute(delete(PasswordReset).where(PasswordReset.user_id==user.id))
            token=secrets.token_urlsafe(48)
            db.session.add(PasswordReset(token_hash=digest(token),user_id=user.id,expires_at=utcnow()+timedelta(minutes=15)))
            send_reset(address,current_app.config['FRONTEND_URL'].rstrip('/')+'/reset-password?token='+token)
            audit('auth.reset_requested',user.id); db.session.commit()
    return jsonify(message='Nếu email đã đăng ký, hướng dẫn đặt lại mật khẩu sẽ được gửi đến bạn.')

@auth.post('/reset-password')
@limiter.limit('10 per hour')
def reset():
    data=payload(); token=text(data.get('token'),'Token',200)
    record=db.session.get(PasswordReset,digest(token))
    if not record or record.used or record.expires_at<utcnow(): raise DomainError('Liên kết không hợp lệ hoặc đã hết hạn.')
    user=get(User,record.user_id,True)
    user.password_hash=generate_password_hash(password(data.get('password'))); record.used=True
    db.session.execute(delete(AuthSession).where(AuthSession.user_id==user.id)); audit('auth.password_reset',user.id); db.session.commit()
    return jsonify(message='Đã đặt lại mật khẩu. Vui lòng đăng nhập.')
