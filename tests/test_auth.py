import pytest

from models import Vendor


@pytest.mark.parametrize(
    ('form', 'message'),
    (
        ({'username': '',           'password': '',             'email': ''},                   b'Vendor name is required.'),
        ({'username': 'Vendor C',   'password': '',             'email': ''},                   b'Password is required.'),
        ({'username': 'Vendor C',   'password': 'password3',    'email': ''},                   b'Vendor email is required.'),
        ({'username': 'Vendor C',   'password': 'password3',    'email': 'vendor.a@email.com'}, b'Email vendor.a@email.com is already taken.')
    )
)
def test_invalid_registering(mock_login, client, form, message):
    """Test all invalid input for registering Vendor C into the database."""
    response = client.post(
        '/register', content_type='multipart/form-data',
        data=form,
        follow_redirects=True
    )
    assert message in response.data


def test_valid_registering(client, app):
    """Tests registering Vendor A into the database."""
    with app.app_context():
        response = client.post(
            '/register', content_type='multipart/form-data',
            data={'username': 'Vendor A', 'password': 'password1', 'email': 'vendor.a@email.com'},
            follow_redirects=True
        )
        assert response.status_code == 200
        vendor: Vendor = Vendor.get(1)
        assert vendor == Vendor(1, 'Vendor A', 'vendor.a@email.com')


@pytest.mark.parametrize(
    ('form', 'message'),
    (
        ({'password': 'password1',      'email': 'notvendor.a@email.com'},  b'Incorrect email.'),
        ({'password': 'notpassword1',   'email': 'vendor.a@email.com'},     b'Incorrect password.')
    )
)
def test_invalid_login(mock_login, client, form, message):
    """Tests all cases where logging in would be invalid for Vendor A."""
    response = client.post('/login', data=form, follow_redirects=True)
    assert message in response.data


def test_invalid_logout(client):
    response = client.post('/logout', follow_redirects=True)
    assert b'Please log in to access this page.' in response.data


def test_valid_login_logout(mock_login, auth, client):
    """Tests logging in Vendor A and logging out Vendor A."""
    assert client.get('/login').status_code == 200
    with client:
        response = auth.login()
        vendor: Vendor = Vendor.current_user()
        assert vendor == Vendor(1, 'Vendor A', 'vendor.a@email.com')
        assert b'Logged in successfully.' in response.data

        response = auth.logout()
        vendor: Vendor = Vendor.current_user()
        assert vendor is None
        assert b'Logged out successfully.' in response.data
