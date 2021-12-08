import os

from flask import Flask

import auth
import models


def create_app(test_config=None) -> Flask:
    # App initialization.
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY='dev', DATABASE=os.path.join(app.instance_path, 'market_db.sqlite'))

    # App configuration.
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.update(test_config)

    # App resource directory.
    if not os.path.exists(app.instance_path):
        app.logger.info('Creating app instance folder [%s].', app.instance_path)
        os.makedirs(app.instance_path)

    @app.route('/hello')
    def hello():
        """A default route for simple testing purposes."""
        return 'Hello World'

    # Login Manager setup
    auth.init_app(app)

    # Database setup.
    import database
    with app.app_context():     # Flask app pre-load tasks. Sets up the database and loads any stateful data required by the system.
        database.init_db()
        models.cache_stalls_from_database()
        models.init_market()
    database.init_app(app)

    # App blueprint assignment.
    import blueprints
    app.register_blueprint(blueprints.auth_blueprint)
    app.register_blueprint(blueprints.inv_blueprint)
    app.register_blueprint(blueprints.shop_blueprint)
    app.register_blueprint(blueprints.market_blueprint)

    # Return the created flask app.
    return app


if __name__ == '__main__':
    create_app().run()
