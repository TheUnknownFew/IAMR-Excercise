import database
from models import Vendor
from models.orders import CustomerCart, CartItem, Order, Transaction, Customer


def test_checkout(mock_bins, client):
    with mock_bins.app_context():
        with client:
            _bin = Vendor.get(1).get_bin(database.gen_uuid(1))
            customer = CustomerCart()
            customer.cart_items[_bin.bin_id] = CartItem(item_bin=_bin, quantity=12.0)
            with client.session_transaction() as session:
                session['customer'] = customer.dict()
            response = client.post(
                '/checkout', content_type='multipart/form-data',
                data={},
                follow_redirects=True
            )
            db = database.get_db()
            customer_item = db.execute("""SELECT * FROM customers WHERE customer_id = ?""", (customer.customer_id,)).fetchone()
            assert Customer(**customer_item) == Customer(customer_id=customer.customer_id)
            order_item = db.execute("""SELECT * FROM orders WHERE customer_id = ?""", (customer.customer_id,)).fetchone()
            assert order_item is not None
            order = Order(**order_item)
            transaction_item = db.execute(
                """SELECT * FROM transactions WHERE order_id = ? AND bin_id = ?""",
                (order.order_id, _bin.bin_id)
            ).fetchone()
            assert Transaction(order_id=order.order_id, bin_id=_bin.bin_id, units_purchased=12.0) == Transaction(*transaction_item)
