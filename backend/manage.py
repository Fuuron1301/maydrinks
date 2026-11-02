"""Local development and database administration; never resets existing databases."""
import os
import sys
import re
from pathlib import Path
import pyodbc
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent/'.env')

def init_database():
    name=os.environ.get('SQLSERVER_DATABASE','MayDrinks')
    if not re.fullmatch(r'MayDrinks(?:Test[A-Za-z0-9_]*)?',name): raise RuntimeError('Only MayDrinks/MayDrinksTest databases can be initialized automatically.')
    server=os.environ.get('SQLSERVER_SERVER',r'(localdb)\MSSQLLocalDB')
    with pyodbc.connect(f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE=master;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;',autocommit=True) as con:
        if not con.execute('SELECT name FROM sys.databases WHERE name = ?',name).fetchone(): con.execute(f'CREATE DATABASE [{name}]')
    print('Database ready:',name)

if __name__=='__main__':
    command=sys.argv[1] if len(sys.argv)>1 else 'serve'
    if command=='init-db': init_database()
    else:
        from maydrinks import create_app
        app=create_app()
        if command=='seed':
            from maydrinks.seed import seed
            with app.app_context(): print(seed()['message']); print('Local credentials: backend/instance/demo-accounts.json')
        elif command=='serve':
            from waitress import serve
            serve(app,host='127.0.0.1',port=int(os.environ.get('PORT','8000')))
        else: raise SystemExit('Use init-db, seed or serve.')
