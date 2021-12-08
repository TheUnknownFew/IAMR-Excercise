import flask

from blueprints.routes import INDEX

blueprint = flask.Blueprint('market', __name__, url_prefix='/market')


@blueprint.route('find', methods=['GET', 'POST'])
def find_market_stall():
    # Todo: Implement user interface and Hook into market.py
    return flask.redirect(flask.url_for(INDEX))


@blueprint.route('configure', methods=['GET', 'POST'])
def configure_market():
    # Todo: Implement user interface and Hook into market.py
    return flask.redirect(flask.url_for(INDEX))
