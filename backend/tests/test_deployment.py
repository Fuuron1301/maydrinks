"""Cross-origin and deployment safety regression tests."""
import pytest
from maydrinks import create_app


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
        raise AssertionError('Render probes must not wake Azure SQL')
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
