from flask_login import LoginManager

from models import Vendor

login_manager = LoginManager()


@login_manager.user_loader
def load_vendor(vendor_id):
    """Required by Flask-Login to load current user session."""
    return Vendor.get(vendor_id)


def init_app(app):
    """Enables Flask-Login in the current app context."""
    login_manager.init_app(app)
    login_manager.login_view = '/login'
