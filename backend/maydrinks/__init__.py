"""Application factory. SQL Server is required; no silent database fallback."""
import os
import re
from urllib.parse import quote_plus
from pathlib import Path
from flask import Flask, jsonify, request, g, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.pool import NullPool
import pyodbc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv
from .models import db
from .domain import DomainError

load_dotenv(Path(__file__).resolve().parents[1] / '.env')
limiter=Limiter(key_func=get_remote_address, default_limits=['300 per minute'])


def sqlserver_connection_string(database=None):
    """Use a complete secret ODBC string, or consistent Windows-auth local settings."""
    explicit = os.environ.get('SQLSERVER_CONNECTION_STRING')
    if explicit:
        if database is not None:
            raise RuntimeError('With SQLSERVER_CONNECTION_STRING, create the target database in SSMS first; then run Alembic. init-db only manages local Windows-auth databases.')
        return explicit
    server = os.environ.get('SQLSERVER_SERVER', r'(localdb)\MSSQLLocalDB')
    name = database or os.environ.get('SQLSERVER_DATABASE', 'MayDrinks')
    if not server.strip() or any(character in server for character in ';{}\r\n'):
        raise RuntimeError('SQLSERVER_SERVER must be a valid local SQL Server instance.')
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,127}', name):
        raise RuntimeError('SQLSERVER_DATABASE must use letters, digits and underscores.')
    return f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={name};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;'


def create_app(config=None):
    app=Flask(__name__)
    if os.environ.get('APP_ENV')=='production' and not os.environ.get('SQLSERVER_CONNECTION_STRING'):
        raise RuntimeError('Production requires SQLSERVER_CONNECTION_STRING for a reachable Microsoft SQL Server.')
    odbc=sqlserver_connection_string()
    production=os.environ.get('APP_ENV')=='production'
    engine_options={'pool_pre_ping':True,'pool_size':5,'max_overflow':5,'pool_recycle':600}
    if production:
        pyodbc.pooling=False
        engine_options={'poolclass':NullPool,'pool_pre_ping':True}
    app.config.update(SQLALCHEMY_DATABASE_URI='mssql+pyodbc:///?odbc_connect='+quote_plus(odbc),SQLALCHEMY_TRACK_MODIFICATIONS=False,SQLALCHEMY_ENGINE_OPTIONS=engine_options,MAX_CONTENT_LENGTH=1024*1024,JSON_AS_ASCII=False,MAIL_MODE=os.environ.get('MAIL_MODE','file'),FRONTEND_URL=os.environ.get('FRONTEND_URL','http://localhost:5173'),RATELIMIT_STORAGE_URI=os.environ.get('RATELIMIT_STORAGE_URI','memory://'))
    if config: app.config.update(config)
    if not app.config['SQLALCHEMY_DATABASE_URI'].startswith('mssql+pyodbc:'): raise RuntimeError('This project requires SQL Server.')
    if os.environ.get('APP_ENV')=='production':
        if app.config['MAIL_MODE'] not in ['smtp','brevo']:
            raise RuntimeError('Production requires SMTP or Brevo HTTPS for password reset delivery.')
        if app.config['MAIL_MODE']=='brevo' and not all(os.environ.get(name) for name in ['BREVO_API_KEY','BREVO_SENDER_EMAIL']):
            raise RuntimeError('Production Brevo email requires BREVO_API_KEY and BREVO_SENDER_EMAIL.')
    app.json.ensure_ascii=False
    db.init_app(app)
    limiter.init_app(app)
    origins=[origin.strip() for origin in os.environ.get('CORS_ORIGINS','http://localhost:5173,http://127.0.0.1:5173,https://maydrinks.surge.sh').split(',') if origin.strip()]
    CORS(app,resources={r'/api/*':{'origins':origins}},allow_headers=['Content-Type','Authorization','Idempotency-Key'],methods=['GET','POST','PUT','PATCH','DELETE','OPTIONS'],supports_credentials=False)

    @app.before_request
    def transaction_lock():
        # SQL Server transaction-scoped mutex serializes business mutations across workers.
        # This small-shop policy prevents check/use races, double deduction and duplicate receipts.
        if request.method in ['POST','PUT','PATCH','DELETE'] and request.path.startswith('/api/') and request.path != '/api/quote':
            result=db.session.execute(text("DECLARE @r int; EXEC @r = sp_getapplock @Resource='MayDrinks.BusinessMutation', @LockMode='Exclusive', @LockOwner='Transaction', @LockTimeout=10000; SELECT @r;")).scalar()
            if result is None or result<0: raise DomainError('Hệ thống đang xử lý đơn khác. Vui lòng thử lại.',409)
    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
        response.headers['Cache-Control']='no-store'
        response.headers['X-Frame-Options']='DENY'
        return response
    @app.errorhandler(DomainError)
    def domain_error(error):
        db.session.rollback()
        return jsonify(error=error.message,details=error.details),error.status
    @app.errorhandler(IntegrityError)
    def integrity_error(error):
        db.session.rollback()
        app.logger.warning('Database constraint violation: %s',type(error.orig).__name__)
        return jsonify(error='Dữ liệu bị trùng hoặc đang được sử dụng. Hãy kiểm tra lại.'),409
    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback(); app.logger.exception('Database request failed')
        return jsonify(error='Không kết nối được cơ sở dữ liệu. Vui lòng thử lại sau.'),503
    @app.errorhandler(HTTPException)
    def http_error(error):
        db.session.rollback()
        return jsonify(error=error.description),error.code
    @app.errorhandler(Exception)
    def unexpected(error):
        db.session.rollback(); app.logger.exception('Unhandled application error')
        return jsonify(error='Đã xảy ra lỗi máy chủ.'),500
    from .auth import auth
    from .api import api
    app.register_blueprint(auth,url_prefix='/api/auth')
    app.register_blueprint(api,url_prefix='/api')
    dist_dir=Path(__file__).resolve().parents[2]/'dist'
    @app.route('/',defaults={'path':''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path.startswith('api/'):
            return jsonify(error='Not Found'),404
        if dist_dir.exists():
            target=(dist_dir/path).resolve()
            if path and target.is_file() and str(target).startswith(str(dist_dir.resolve())):
                return send_from_directory(dist_dir,path)
            if (dist_dir/'index.html').is_file():
                return send_from_directory(dist_dir,'index.html')
        return jsonify(error='Not Found'),404
    return app
