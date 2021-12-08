import flask

import database
from blueprints.routes import ADD_TO_CART, DISPLAY_CART, INDEX
from models import Vendor, Bin
from models.orders import CustomerCart, CartItem, Order, Transaction

blueprint = flask.Blueprint('orders', __name__)


"""
Future considerations:
Current implementation shows all vendors on one page along with all the products
you can buy from a vendor.

To better emulate a real farmer's market, a design more ingrained into the market
map could be implemented where the customer has to traverse the map in order to view
vendor wares.

Due to time considerations, the former was implemented, but the latter is still feasible
to implement with the given system.
"""


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    """The main front facing shop."""

    if flask.request.method == 'POST':
        if 'customer' not in flask.session:
            # A customer corresponds to the current session since there is no customer login.
            # I.e. A customer is a browsing session.
            flask.session['customer'] = CustomerCart().dict()
        flask.session['bin_clicked'] = Bin.from_json(flask.request.form['bin_data'])
        return flask.redirect(flask.url_for(ADD_TO_CART))

    # If promoted vendors were implemented, order of promoted vendors would be determined here.
    vendors = Vendor.get_all_vendors() or []
    vendor_bins = [{'vendor': vendor, 'bins': [_bin for _bin in vendor.bins]} for vendor in vendors]
    return flask.render_template('shop/browse.html', shop=vendor_bins)


@blueprint.route('/cart', methods=['GET'])
def display_cart():
    """Display the current user's cart."""
    if 'bin_clicked' in flask.session:
        return flask.redirect(flask.url_for(ADD_TO_CART))
    if 'customer' in flask.session:
        cart: CustomerCart = CustomerCart(**flask.session['customer'])
        return flask.render_template('shop/cart.html', cart=cart.cart_items, total_price=cart.cart_total)
    else:
        return flask.render_template('shop/cart.html')


@blueprint.route('/remove-cart', methods=['GET'])
def remove_item():
    if 'customer' in flask.session:
        cart: CustomerCart = CustomerCart.parse_obj(flask.session['customer'])
        bin_id = flask.request.args['bin_id']
        if bin_id in cart.cart_items:
            cart.cart_items.pop(bin_id)
            flask.session['customer'] = cart.dict()
    return flask.redirect(flask.url_for(DISPLAY_CART))


@blueprint.route('/add-cart', methods=['GET', 'POST'])
def add_to_cart():
    """Add an item to the current user's cart."""
    if 'bin_clicked' not in flask.session or 'customer' not in flask.session:
        return flask.redirect(flask.url_for(DISPLAY_CART))

    bin_clicked: Bin = Bin(**flask.session['bin_clicked'])
    cart: CustomerCart = CustomerCart.parse_obj(flask.session['customer'])
    if flask.request.method == 'POST':
        if 'canceled' in flask.request.form:
            flask.session.pop('bin_clicked')
            return flask.redirect(flask.url_for(DISPLAY_CART))

        quantity = float(flask.request.form['quantity'])
        if bin_clicked.bin_id in cart.cart_items:
            cart.cart_items[bin_clicked.bin_id].quantity += quantity
        else:
            cart.cart_items[bin_clicked.bin_id] = CartItem(item_bin=bin_clicked, quantity=quantity)
        flask.session['customer'] = cart.dict()
        flask.session.pop('bin_clicked')
        return flask.redirect(flask.url_for(DISPLAY_CART))
    return flask.render_template('shop/cart.html', bin_clicked=bin_clicked, cart=cart.cart_items, total_price=cart.cart_total)


@blueprint.route('/checkout', methods=['POST'])
def checkout():
    if 'customer' not in flask.session:
        return flask.redirect(flask.url_for(INDEX))
    cart: CustomerCart = CustomerCart.parse_obj(flask.session['customer'])
    if len(cart.cart_items) == 0:
        return flask.redirect(flask.url_for(INDEX))

    db = database.get_db()
    is_subscribed = 'is_subscribed' in flask.session
    customer_email = flask.session.get('customer_email')
    customer_name = flask.session.get('customer_name')
    customer_exists = db.execute(
        """SELECT customer_id FROM customers WHERE customer_id = ?""",
        (cart.customer_id,)
    ).fetchone()
    if customer_exists is None:
        db.execute(
            """INSERT INTO customers(customer_id, name, email, newsletter_subscription) VALUES (?, ?, ?, ?)""",
            (cart.customer_id, customer_name, customer_email, is_subscribed)
        )
    for cart_item in cart.cart_items.values():
        order = Order(customer_id=cart.customer_id)
        transaction = Transaction(bin_id=cart_item.item_bin.bin_id, order_id=order.order_id, units_purchased=cart_item.quantity)
        db.execute("""INSERT INTO orders(customer_id, order_id, order_filled, order_filled_at) VALUES (?, ?, ?, ?)""", order.tuple())
        db.execute(
            """
            INSERT INTO transactions(order_id, bin_id, units_purchased, transaction_filled, time_of_sale, transaction_filled_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            transaction.tuple()
        )
    db.commit()
    cart.cart_items.clear()
    flask.session['customer'] = cart.dict()
    return flask.redirect(flask.url_for(INDEX))
