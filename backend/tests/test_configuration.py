"""Local SQL configuration, CLI safety, CORS and optional email regressions."""
import pytest
from maydrinks import create_app, sqlserver_connection_string


def test_surge_origin_allowed():
    app = create_app()
    response = app.test_client().options('/api/health', headers={
        'Origin': 'https://maydrinks.surge.sh',
        'Access-Control-Request-Method': 'GET',
    })
    assert response.headers.get('Access-Control-Allow-Origin') == 'https://maydrinks.surge.sh'


def test_readiness_does_not_query_database(monkeypatch):
    app = create_app()
    def no_query(*_args, **_kwargs):
        raise AssertionError('Process readiness must not query SQL Server')
    monkeypatch.setattr('maydrinks.models.db.session.execute', no_query)
    result = app.test_client().get('/api/ready')
    assert result.status_code == 200
    assert result.json == {'status': 'ready'}


def test_unknown_origin_rejected():
    app = create_app()
    response = app.test_client().options('/api/health', headers={
        'Origin': 'https://untrusted.example',
        'Access-Control-Request-Method': 'GET',
    })
    assert 'Access-Control-Allow-Origin' not in response.headers


def test_production_requires_remote_sqlserver(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.delenv('SQLSERVER_CONNECTION_STRING', raising=False)
    with pytest.raises(RuntimeError, match='SQLSERVER_CONNECTION_STRING'):
        create_app()


def test_production_requires_brevo_credentials(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('SQLSERVER_CONNECTION_STRING', 'DRIVER={ODBC Driver 18 for SQL Server};SERVER=example.org;DATABASE=MayDrinks;')
    monkeypatch.setenv('MAIL_MODE', 'brevo')
    monkeypatch.delenv('BREVO_API_KEY', raising=False)
    monkeypatch.delenv('BREVO_SENDER_EMAIL', raising=False)
    with pytest.raises(RuntimeError, match='BREVO_API_KEY'):
        create_app()


def test_brevo_reset_sent_over_https(monkeypatch):
    import json
    from maydrinks.auth import send_reset

    monkeypatch.setenv('BREVO_API_KEY', 'test-key')
    monkeypatch.setenv('BREVO_SENDER_EMAIL', 'verified@example.org')
    app = create_app({'MAIL_MODE': 'brevo'})
    calls = []

    class Accepted:
        status = 201
        def __enter__(self): return self
        def __exit__(self, *_): pass

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return Accepted()

    monkeypatch.setattr('maydrinks.auth.urlopen', fake_urlopen)
    with app.app_context():
        send_reset('customer@example.org', 'https://maydrinks.surge.sh/reset-password?token=secret')
    request, timeout = calls[0]
    assert request.full_url == 'https://api.brevo.com/v3/smtp/email'
    assert request.get_header('Api-key') == 'test-key'
    assert timeout == 15
    body = json.loads(request.data)
    assert body['to'] == [{'email': 'customer@example.org'}]
    assert 'token=secret' in body['textContent']


def test_brevo_mail_error_does_not_expose_token(monkeypatch):
    from urllib.error import HTTPError
    from maydrinks.auth import send_reset
    from maydrinks.domain import DomainError

    monkeypatch.setenv('BREVO_API_KEY', 'test-key')
    monkeypatch.setenv('BREVO_SENDER_EMAIL', 'verified@example.org')
    app = create_app({'MAIL_MODE': 'brevo'})
    def fail(*_args, **_kwargs):
        raise HTTPError('https://api.brevo.com/v3/smtp/email', 401, 'unauthorized', {}, None)
    monkeypatch.setattr('maydrinks.auth.urlopen', fail)
    with app.app_context(), pytest.raises(DomainError) as error:
        send_reset('customer@example.org', 'https://maydrinks.surge.sh/reset-password?token=secret')
    assert error.value.status == 503
    assert 'secret' not in error.value.message


def test_local_database_settings_shared_with_app(monkeypatch):
    from sqlalchemy.engine import make_url
    monkeypatch.delenv('SQLSERVER_CONNECTION_STRING', raising=False)
    monkeypatch.setenv('SQLSERVER_SERVER', r'.\SQLEXPRESS')
    monkeypatch.setenv('SQLSERVER_DATABASE', 'MayDrinksTest_Config')
    app = create_app()
    configured = make_url(app.config['SQLALCHEMY_DATABASE_URI']).query['odbc_connect']
    assert configured == sqlserver_connection_string()
    assert r'SERVER=.\SQLEXPRESS;' in configured
    assert 'DATABASE=MayDrinksTest_Config;' in configured
    assert 'DATABASE=master;' in sqlserver_connection_string(database='master')


def test_full_connection_string_takes_precedence(monkeypatch):
    explicit = 'DRIVER={ODBC Driver 18 for SQL Server};SERVER=sql.example.org;DATABASE=MayDrinks;'
    monkeypatch.setenv('SQLSERVER_CONNECTION_STRING', explicit)
    monkeypatch.setenv('SQLSERVER_SERVER', 'ignored')
    assert sqlserver_connection_string() == explicit


@pytest.mark.parametrize('key,value', [
    ('SQLSERVER_SERVER', 'localhost;DATABASE=unexpected'),
    ('SQLSERVER_DATABASE', 'MayDrinks;DROP DATABASE master'),
])
def test_invalid_local_sql_settings_rejected(monkeypatch, key, value):
    monkeypatch.delenv('SQLSERVER_CONNECTION_STRING', raising=False)
    monkeypatch.setenv(key, value)
    with pytest.raises(RuntimeError, match='SQLSERVER_'):
        sqlserver_connection_string()


def test_init_db_does_not_create_unintended_remote_database(monkeypatch):
    import manage
    monkeypatch.setenv('SQLSERVER_CONNECTION_STRING', 'SERVER=remote.example.org;DATABASE=MayDrinks;')
    with pytest.raises(RuntimeError, match='SSMS'):
        manage.init_database()


def test_check_command_reads_current_sql_schema(app, capsys):
    import manage
    manage.check_database(app)
    output = capsys.readouterr().out
    assert 'SQL Server connection: OK' in output
    assert 'fc2a96045963 (head)' in output
    assert 'drinks: 16' in output


def test_seed_again_preserves_existing_demo_records(app):
    from sqlalchemy import select, func
    from maydrinks.models import db, User, Order
    from maydrinks.seed import seed
    with app.app_context():
        password_hash = db.session.get(User, 'user-admin').password_hash
        before = db.session.scalar(select(func.count()).select_from(Order))
        assert 'no existing data changed' in seed()['message']
        assert db.session.get(User, 'user-admin').password_hash == password_hash
        assert db.session.scalar(select(func.count()).select_from(Order)) == before
