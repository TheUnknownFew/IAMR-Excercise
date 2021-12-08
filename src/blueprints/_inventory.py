import flask
from flask_login import login_required

import models
from blueprints.routes import DISPLAY_INVENTORY, INDEX
from models import Vendor

blueprint = flask.Blueprint('inventory', __name__, url_prefix='/inventory')


@blueprint.route('/', methods=['GET'])
@login_required
def display_inventory():
    vendor = Vendor.current_user()
    return flask.render_template('inventory/inventory.html', vendor=vendor, bins=vendor.bins)


@blueprint.route('/create', methods=['GET', 'POST'])
@login_required
def create_inventory_bin():
    if flask.request.method == 'POST':
        product_name = flask.request.form['product_name']
        stock = flask.request.form['stock']
        unit_price = flask.request.form['unit_price']
        price_code = flask.request.form['price_code']
        Vendor.current_user().create_bin(product_name, float(stock), float(unit_price), models.PriceCode[price_code])
        return flask.redirect(flask.url_for(DISPLAY_INVENTORY))
    return flask.render_template('inventory/bin_edit.html', authenticated_view='Yes', edit_mode=False, bin=None, price_codes=models.price_codes())


@blueprint.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_inventory_bin():
    if flask.request.method == 'POST':
        bin_id = flask.request.form['bin_id']
        product_name = flask.request.form['product_name']
        stock = flask.request.form['stock']
        unit_price = flask.request.form['unit_price']
        price_code = flask.request.form['price_code']
        Vendor.current_user().update_bin(
            bin_id=bin_id,
            product_name=product_name,
            stock=float(stock),
            price=(float(unit_price), models.PriceCode[price_code])
        )
        return flask.redirect(flask.url_for(DISPLAY_INVENTORY))
    bin_id = flask.request.args['bin_id']
    _bin = Vendor.current_user().get_bin(bin_id)
    return flask.render_template('inventory/bin_edit.html', edit_mode=True, bin=_bin, price_codes=models.price_codes())


@blueprint.route('/remove', methods=['POST'])
@login_required
def remove_inventory_bin():
    vendor = Vendor.current_user()
    vendor.remove_bin(flask.request.form['bin_id'])
    return flask.redirect(flask.url_for(DISPLAY_INVENTORY))


@blueprint.route('/sales', methods=['GET', 'POST'])
def sales():
    # todo: generate and display all pending and fulfilled orders.
    # call vendor.get_all_orders, display all orders along with their transactions, provide fill buttons if transaction
    # not filled, and fill the whole order when every transaction in the order is filled. Display previous filled orders
    # and transactions.
    # Update the database as necessary.
    return flask.redirect(flask.url_for(INDEX))


@blueprint.route('/report', methods=['GET', 'POST'])
def generate_report():
    # todo: generate analysis and performance report.
    return flask.redirect(flask.url_for(INDEX))
