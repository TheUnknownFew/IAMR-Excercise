import os
import tempfile
from datetime import datetime

import pytest
from werkzeug.security import generate_password_hash

import database
from app import create_app
from models import MarketMap


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({'TESTING': True, 'DATABASE': db_path})

    with app.app_context():
        database.init_db()
    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def mock_login(app):
    test_data = [
        ('Vendor A', generate_password_hash('password1'), 'vendor.a@email.com'),    # 1
        ('Vendor B', generate_password_hash('password2'), 'vendor.b@email.com'),    # 2
        ('Vendor C', generate_password_hash('password3'), 'vendor.c@email.com')     # 3
    ]
    with app.app_context():
        db = database.get_db()
        for data in test_data:
            db.execute(
                """INSERT INTO vendors(vendor_name, vendor_secret, vendor_email) VALUES (?, ?, ?)""",
                data
            )
        db.commit()
    yield app


@pytest.fixture
def mock_bins(mock_login):
    test_data = [
        (database.gen_uuid(1), 1, 'apple', 5.0, 5.0, 'USD'),
        (database.gen_uuid(2), 1, 'orange', 3.0, 2.3, 'USD'),
        (database.gen_uuid(3), 1, 'grape', 3.0, 2.3, 'USD'),
        (database.gen_uuid(4), 2, 'rice', 13.5, 100.0, 'YEN'),
        (database.gen_uuid(5), 2, 'soy sauce', 10.2, 20.44, 'YEN'),
        (database.gen_uuid(6), 3, 'carrot', 12.0, 20.0, 'USD'),
        (database.gen_uuid(7), 3, 'cabbage', 12.0, 20.0, 'USD')
    ]
    with mock_login.app_context():
        db = database.get_db()
        for data in test_data:
            db.execute(
                """INSERT INTO bins(bin_id, vendor_id, product_name, stock, unit_price, price_code) VALUES (?, ?, ?, ?, ?, ?)""",
                data
            )
        db.commit()
    yield mock_login


@pytest.fixture
def mock_map(mock_bins):
    # Create a mock map
    test_data = [
        (database.gen_uuid(6), database.gen_uuid(2), 2.0),
        (database.gen_uuid(2), database.gen_uuid(1), 7.5),
        (database.gen_uuid(1), database.gen_uuid(4), 5.0),
        (database.gen_uuid(1), database.gen_uuid(5), 2.5),
        (database.gen_uuid(4), database.gen_uuid(5), 10.0),
        (database.gen_uuid(5), database.gen_uuid(3), 5.5),
        (database.gen_uuid(5), database.gen_uuid(7), 12.3)
    ]
    with mock_bins.app_context():
        db = database.get_db()
        for data in test_data:
            db.execute(
                """INSERT INTO market_map(vendor_bin_id, neighbor_bin_id, unit_distance) VALUES (?, ?, ?)""",
                data
            )
        MarketMap.cache_stalls_from_database()
        db.commit()
        yield mock_bins


@pytest.fixture
def mock_customers(mock_bins):
    test_data = [
        # customer_id,         name, email, newsletter_subscription
        (database.gen_uuid(1), None, None, False),
        (database.gen_uuid(2), 'Alex', 'myemail@email.com', True),
        (database.gen_uuid(3), None, None, False)
    ]
    with mock_bins.app_context():
        db = database.get_db()
        for data in test_data:
            db.execute(
                """INSERT INTO customers(customer_id, name, email, newsletter_subscription) VALUES (?, ?, ?, ?)""",
                data
            )
        db.commit()
        yield mock_bins


@pytest.fixture
def mock_orders(mock_customers):
    test_orders = [
        # order_id,            customer_id,         filled, filled_at
        (database.gen_uuid(1), database.gen_uuid(1), False, None),
        (database.gen_uuid(2), database.gen_uuid(2), False, None),
        (database.gen_uuid(3), database.gen_uuid(3), False, None)
    ]
    test_transactions = [
        # order_id, bin_id, units_purchased, transaction_filled, time_of_sale, transaction_filled_at
        (database.gen_uuid(1), database.gen_uuid(1), 3.0, False, datetime.now(), None),
        (database.gen_uuid(1), database.gen_uuid(2), 5.0, False, datetime.now(), None),
        (database.gen_uuid(1), database.gen_uuid(3), 6.0, False, datetime.now(), None),
        (database.gen_uuid(2), database.gen_uuid(1), 3.0, False, datetime.now(), None),
        (database.gen_uuid(3), database.gen_uuid(6), 4.0, False, datetime.now(), None)
    ]

    with mock_customers.app_context():
        db = database.get_db()
        for data in test_orders:
            db.execute(
                """INSERT INTO orders(order_id, customer_id, order_filled, order_filled_at) VALUES (?, ?, ?, ?)""",
                data
            )
        db.commit()
        for data in test_transactions:
            db.execute(
                """INSERT INTO transactions(order_id, bin_id, units_purchased, transaction_filled, time_of_sale, transaction_filled_at) VALUES (?, ?, ?, ?, ?, ?)""",
                data
            )
        db.commit()
        yield mock_customers


class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, email='vendor.a@email.com', password='password1'):
        return self._client.post(
            '/login', content_type='multipart/form-data',
            data={'email': email, 'password': password},
            follow_redirects=True
        )

    def logout(self):
        return self._client.post('/logout', follow_redirects=True)


@pytest.fixture
def auth(client):
    return AuthActions(client)


@pytest.fixture
def client(app):
    return app.test_client()
