"""Local development and database administration; never resets existing databases."""
import argparse
import os
import re
import sys
from pathlib import Path

import pyodbc
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError

from maydrinks import create_app, sqlserver_connection_string
from maydrinks.models import db, Drink, Ingredient, Order

def init_database():
    name = os.environ.get('SQLSERVER_DATABASE', 'MayDrinks')
    if not re.fullmatch(r'MayDrinks(?:Test[A-Za-z0-9_]*)?', name):
        raise RuntimeError('Only MayDrinks/MayDrinksTest databases can be initialized automatically.')
    connection_string = sqlserver_connection_string(database='master')
    with pyodbc.connect(connection_string, autocommit=True) as connection:
        if not connection.execute('SELECT name FROM sys.databases WHERE name = ?', name).fetchone():
            connection.execute(f'CREATE DATABASE [{name}]')
    print('Database ready:', name)


def check_database(app):
    """Read-only diagnostics; never print credentials or silently create schema."""
    with app.app_context():
        database = db.session.execute(text('SELECT DB_NAME()')).scalar_one()
        revision = MigrationContext.configure(db.session.connection()).get_current_revision()
        config = Config(str(Path(__file__).parent / 'alembic.ini'))
        heads = ScriptDirectory.from_config(config).get_heads()
        if revision not in heads:
            raise RuntimeError('Database schema is not current. Run Alembic upgrade head before seed/serve.')
        print('SQL Server connection: OK')
        print('Database:', database)
        print('Alembic revision:', revision, '(head)')
        for model in (Drink, Ingredient, Order):
            count = db.session.scalar(select(func.count()).select_from(model))
            print(f'{model.__tablename__}: {count}')

def main(argv=None):
    parser = argparse.ArgumentParser(description='May Drinks local SQL Server tools; no automatic reset.')
    parser.add_argument('command', nargs='?', default='serve', choices=['init-db', 'check', 'seed', 'serve'])
    args = parser.parse_args(argv)
    try:
        if args.command == 'init-db':
            init_database()
            return 0
        app = create_app()
        if args.command == 'check':
            check_database(app)
        elif args.command == 'seed':
            from maydrinks.seed import seed
            with app.app_context():
                print(seed()['message'])
                credentials = Path(app.instance_path) / 'demo-accounts.json'
                if credentials.exists():
                    print('Local credentials:', credentials)
                else:
                    print('No credential file on this machine; existing passwords were not changed.')
        else:
            from waitress import serve
            print('API: http://127.0.0.1:' + os.environ.get('PORT', '8000'))
            serve(app, host='127.0.0.1', port=int(os.environ.get('PORT', '8000')))
        return 0
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
    except (pyodbc.Error, SQLAlchemyError):
        print('SQL Server unavailable or schema missing. Check ODBC Driver 18, SQL instance, database permissions and Alembic migration. See README troubleshooting.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    raise SystemExit(main())
