import pytest

import database
from models import Bin, Vendor, PriceCode
from models.orders import Order, Transaction


@pytest.mark.parametrize(
    ('product_name', 'initial_stock', 'unit_price', 'price_code'),
    (
        ('apple', 5.0, 5.0, PriceCode.USD),
    )
)
def test_create_get_bin(mock_login, auth, client, product_name, initial_stock, unit_price, price_code):
    with mock_login.app_context():
        with client:
            auth.login()
            vendor = Vendor.current_user()
            _bin = vendor.create_bin(product_name, initial_stock, unit_price, price_code)
            assert _bin == vendor.get_bin(_bin.bin_id), 'Created bin does not match after fetching the bin from the ven'
            auth.logout()


@pytest.mark.parametrize(
    ('product_name', 'stock', 'price', 'expected'),
    (
        (None, None, None, None),
        ('grape', None, None, {'bin_id': database.gen_uuid(1), 'vendor_id': 1, 'product_name': 'grape', 'stock': 5.0, 'unit_price': 5.0, 'price_code': 'USD'}),
        (None, 100.0, None, {'bin_id': database.gen_uuid(1), 'vendor_id': 1, 'product_name': 'apple', 'stock': 100.0, 'unit_price': 5.0, 'price_code': 'USD'}),
        (None, None, (500.0, PriceCode.YEN), {'bin_id': database.gen_uuid(1), 'vendor_id': 1, 'product_name': 'apple', 'stock': 5.0, 'unit_price': 500.0, 'price_code': 'YEN'}),
        ('grape', None, (500.0, PriceCode.YEN), {'bin_id': database.gen_uuid(1), 'vendor_id': 1, 'product_name': 'grape', 'stock': 5.0, 'unit_price': 500.0, 'price_code': 'YEN'}),
        ('grape', 100.0, (500.0, PriceCode.YEN), {'bin_id': database.gen_uuid(1), 'vendor_id': 1, 'product_name': 'grape', 'stock': 100.0, 'unit_price': 500.0, 'price_code': 'YEN'})
    )
)
def test_update_bin(mock_bins, auth, client, product_name, stock, price, expected):
    with mock_bins.app_context():
        with client:
            auth.login()
            vendor = Vendor.current_user()
            _bin = vendor.update_bin(database.gen_uuid(1), product_name=product_name, stock=stock, price=price)
            if not expected:
                assert _bin is None
            else:
                assert _bin == Bin(**expected)
            auth.logout()


@pytest.mark.parametrize(
    ('vendor_id', 'size', 'login', 'vendor_bins'),
    (
        (1, 3, {'email': 'vendor.a@email.com', 'password': 'password1'},
         [{'bin_id': database.gen_uuid(1), 'vendor_id': 1, 'product_name': 'apple', 'stock': 5.0, 'unit_price': 5.0,  'price_code': 'USD'},
          {'bin_id': database.gen_uuid(2), 'vendor_id': 1, 'product_name': 'orange', 'stock': 3.0, 'unit_price': 2.3, 'price_code': 'USD'},
          {'bin_id': database.gen_uuid(3), 'vendor_id': 1, 'product_name': 'grape', 'stock': 3.0, 'unit_price': 2.3, 'price_code': 'USD'}]),
        (2, 2, {'email': 'vendor.b@email.com', 'password': 'password2'},
         [{'bin_id': database.gen_uuid(4), 'vendor_id': 2, 'product_name': 'rice', 'stock': 13.5, 'unit_price': 100.0, 'price_code': 'YEN'},
          {'bin_id': database.gen_uuid(5), 'vendor_id': 2, 'product_name': 'soy sauce', 'stock': 10.2, 'unit_price': 20.44, 'price_code': 'YEN'}])
    )
)
def test_get_all_bins(mock_bins, auth, client, vendor_id, size, login, vendor_bins):
    with mock_bins.app_context():
        with client:
            auth.login(**login)
            vendor = Vendor.current_user()
            bins = vendor.bins
            assert len(bins) == size
            # Test if all bins returned from vendor.bins are all the expected bins populated in the database.
            for actual, expected in zip(bins, vendor_bins):
                b = Bin(**expected)
                assert actual == b, 'Actual vs expected bin do not match.'
                assert vendor.get_bin(b.bin_id) == b, 'Fetching individual bin does not match expected bin.'
            auth.logout()


@pytest.mark.parametrize(
    ('vendor_id', 'login', 'vendor_bin_id', 'unauthorized_vendor'),
    (
        (1, {'email': 'vendor.a@email.com', 'password': 'password1'}, database.gen_uuid(1), 2),
    )
)
def test_invalid_update_create_remove(mock_bins, auth, client, vendor_id, login, vendor_bin_id, unauthorized_vendor):
    with mock_bins.app_context():
        auth.login(**login)
        with pytest.raises(RuntimeError) as err:
            _ = Vendor.get(unauthorized_vendor).remove_bin(vendor_bin_id)
        # Test if the vendor under the current context is not authorized.
        assert 'Working outside of request context.' in str(err.value), 'Vendor authorized in an unauthorized context.'
        with pytest.raises(RuntimeError) as err:
            _ = Vendor.get(unauthorized_vendor).create_bin('juice', 3.0, 1.11, PriceCode.USD)
        # Test if the vendor under the current context is not authorized.
        assert 'Working outside of request context.' in str(err.value), 'Vendor authorized in an unauthorized context.'
        with pytest.raises(RuntimeError) as err:
            _ = Vendor.get(unauthorized_vendor).update_bin(vendor_bin_id, product_name='cream')
        # Test if the vendor under the current context is not authorized.
        assert 'Working outside of request context.' in str(err.value), 'Vendor authorized in an unauthorized context.'
        auth.logout()


@pytest.mark.parametrize(
    ('vendor_id', 'login', 'orders'),
    (
        (1, {'email': 'vendor.a@email.com', 'password': 'password1'},
         [
             (Order(database.gen_uuid(1), database.gen_uuid(1)), [Transaction(database.gen_uuid(1), database.gen_uuid(1), 3.0, False), Transaction(database.gen_uuid(1), database.gen_uuid(2), 5.0, False), Transaction(database.gen_uuid(1), database.gen_uuid(3), 6.0, False)]),
             (Order(database.gen_uuid(2), database.gen_uuid(2)), [Transaction(database.gen_uuid(2), database.gen_uuid(1), 3.0, False)])
         ]),
        (3, {'email': 'vendor.c@email.com', 'password': 'password3'},
         [
             (Order(database.gen_uuid(3), database.gen_uuid(3)), [Transaction(database.gen_uuid(3), database.gen_uuid(6), 4.0, False)])
         ])
    )
)
def test_get_all_orders(mock_orders, auth, client, vendor_id, login, orders):
    with mock_orders.app_context():
        with client:
            auth.login(**login)
            vendor = Vendor.get(vendor_id)
            orders_vendor_has = vendor.get_all_orders()
            for order, transactions in orders:
                assert order in orders_vendor_has
                for transaction in transactions:
                    assert transaction in orders_vendor_has[order]
            auth.logout()
