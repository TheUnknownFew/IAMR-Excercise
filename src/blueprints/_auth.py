import sqlite3
from typing import Union

import flask
from flask_login import login_required, logout_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash

import database
from blueprints.routes import LOGIN, DISPLAY_INVENTORY
from models import Vendor

blueprint = flask.Blueprint('auth', __name__)


def validate_vendor_registry(db: sqlite3.Connection) -> tuple[bool, Union[str, tuple[str, str, str]]]:
    """Validates values sent to the register form."""
    vendor_name = flask.request.form['username']
    if not vendor_name or vendor_name == '':
        return False, 'Vendor name is required.'
    vendor_secret = flask.request.form['password']
    if not vendor_secret or vendor_secret == '':
        return False, 'Password is required.'
    vendor_email = flask.request.form['email']
    if not vendor_email or vendor_email == '':
        return False, 'Vendor email is required.'

    vendor_exists = db.execute("""SELECT vendor_id FROM vendors WHERE vendor_email = ?""", (vendor_email,)).fetchone()
    if vendor_exists:
        return False, f'Email {vendor_email} is already taken.'
    return True, (vendor_name, generate_password_hash(vendor_secret), vendor_email)


def validate_login(db: sqlite3.Connection) -> tuple[bool, Union[str, Vendor]]:
    """Validates values sent to the login form."""
    form = flask.request.form
    vendor = db.execute("""SELECT * FROM vendors WHERE vendor_email = ?""", (form['email'],)).fetchone()
    if not vendor:
        return False, 'Incorrect email.'
    if not check_password_hash(vendor['vendor_secret'], form['password']):
        return False, 'Incorrect password.'
    return True, Vendor.get(vendor['vendor_id'])


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    """Registers a new vendor to the database or asks a vendor to register."""
    if flask.request.method == 'POST':
        db = database.get_db()
        is_valid, data = validate_vendor_registry(db)
        if is_valid:
            db.execute("""INSERT INTO vendors(vendor_name, vendor_secret, vendor_email) VALUES (?, ?, ?)""", (*data,))
            db.commit()
            flask.flash('Vendor successfully registered.')
            return flask.redirect(flask.url_for(LOGIN))
        flask.flash(data)
    return flask.render_template('auth/register.html')


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    """Logs in a registered vendor to the current vendor session. Handled by Flask-Login."""
    if flask.request.method == 'POST':
        db = database.get_db()
        is_valid, data = validate_login(db)
        if is_valid:
            # Future consideration would be to only clear the session on logout.
            # That way information is kept if you forgot to log in before doing actions.
            flask.session.clear()
            login_user(data)
            flask.flash('Logged in successfully.')
            return flask.redirect(flask.url_for(DISPLAY_INVENTORY))
        flask.flash(data)
    return flask.render_template('auth/login.html')


@blueprint.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Logs out the current vendor session. Handled by Flask-Login."""
    flask.session.clear()
    logout_user()
    flask.flash('Logged out successfully.')
    return flask.redirect(flask.url_for(LOGIN))
