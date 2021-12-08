import sqlite3

import pytest

import database


def test_get_close_db(app):
    # Test if the first call to get_db equals the second call
    # to get_db since the first call will open a new connection.
    with app.app_context():
        db = database.get_db()
        assert db is database.get_db()

    with pytest.raises(sqlite3.ProgrammingError) as err:
        db.execute('SELECT 1')

    assert 'closed' in str(err.value)
