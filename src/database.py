import sqlite3
import uuid

from flask import current_app, g


def gen_uuid(int_val: int = None) -> str:
    """Convenience function for making random uuids or uuids from a given int value."""
    if int_val:
        return str(uuid.UUID(int=int_val, version=4))
    return str(uuid.uuid4())


def get_db() -> sqlite3.Connection:
    """
    Returns the current connection to the app's sqlite database.
    Opens a new connection if there is no current connection.
    :return: The connection to the app's sqlite database.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(err=None):
    """
    Closes the current connection to the database.
    :param err: A supplied error from the Flask app's teardown call.
    :return: Returns True if the current connection was successfully closed.
             Returns False if there is no current connection.
    """
    db: sqlite3.Connection = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """
    Initializes the app's database with a supplied schema from file.
    This Python code assumes that the schema loaded creates tables as
    long as they do not exist.
    """
    db = get_db()
    with current_app.open_resource('sql/schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


def init_app(app):
    """
    Registers the database closing action to the app's teardown stage.
    This ensures that the database is always closed when the app shuts down.
    :param app: The Flask app with a database.
    """
    app.logger.info('Database shutdown registered to app teardown.')
    app.teardown_appcontext(close_db)
