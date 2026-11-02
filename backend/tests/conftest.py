"""SQL Server-only tests, isolated from the running demo and production database."""
import importlib
import os
import re
from pathlib import Path
from uuid import uuid4

import pyodbc
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete
from werkzeug.security import generate_password_hash

from maydrinks import create_app
from maydrinks.models import db


@pytest.fixture(scope='session')
def test_database():
    if os.environ.get('APP_ENV') == 'production':
        pytest.fail('Never run integration tests with APP_ENV=production.')
    previous = os.environ.get('SQLSERVER_CONNECTION_STRING')
    explicit = os.environ.get('TEST_SQLSERVER_CONNECTION_STRING')
    master = None
    if explicit:
        match = re.search(r'(?:^|;)\s*(?:DATABASE|Initial Catalog)\s*=\s*([^;]+)', explicit, re.I)
        if not match or not re.fullmatch(r'MayDrinksTest_[A-Za-z0-9_]+', match.group(1).strip()):
            pytest.fail('TEST_SQLSERVER_CONNECTION_STRING must name a dedicated MayDrinksTest_* database.')
        connection_string = explicit
    else:
        if os.name != 'nt':
            pytest.fail('Set TEST_SQLSERVER_CONNECTION_STRING to a dedicated SQL Server MayDrinksTest_* database.')
        database_name = 'MayDrinksTest_' + uuid4().hex[:12]
        master_string = r'DRIVER={ODBC Driver 18 for SQL Server};SERVER=(localdb)\MSSQLLocalDB;DATABASE=master;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;'
        master = pyodbc.connect(master_string, autocommit=True)
        master.execute(f'CREATE DATABASE [{database_name}]')
        connection_string = master_string.replace('DATABASE=master;', f'DATABASE={database_name};')
    os.environ['SQLSERVER_CONNECTION_STRING'] = connection_string
    try:
        backend = Path(__file__).resolve().parents[1]
        config = Config(str(backend / 'alembic.ini'))
        config.set_main_option('script_location', str(backend / 'migrations'))
        command.upgrade(config, 'head')
        yield connection_string
    finally:
        if previous is None:
            os.environ.pop('SQLSERVER_CONNECTION_STRING', None)
        else:
            os.environ['SQLSERVER_CONNECTION_STRING'] = previous
        if master is not None:
            master.execute(f'ALTER DATABASE [{database_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE')
            master.execute(f'DROP DATABASE [{database_name}]')
            master.close()


@pytest.fixture
def app(test_database, monkeypatch):
    app = create_app({'TESTING': True, 'RATELIMIT_ENABLED': False, 'MAIL_MODE': 'file'})
    seed_module = importlib.import_module('maydrinks.seed')
    # Test data is never deployed. A cheap hash keeps fixture setup fast; production uses scrypt.
    monkeypatch.setattr(seed_module, 'generate_password_hash', lambda value: generate_password_hash(value, method='pbkdf2:sha256:1000'))
    monkeypatch.setenv('DEMO_PASSWORD', 'TestOnly12345')
    with app.app_context():
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(delete(table))
        db.session.commit()
        seed_module.seed()
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()
