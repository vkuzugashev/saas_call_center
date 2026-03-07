import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, String, Integer, Column, JSON

load_dotenv()

db_user = os.environ.get('DB_USERNAME', 'root')
db_pwd = os.environ.get('DB_PWD', '1234567')
db_host = os.environ.get('DB_HOST', 'localhost')
db_port = os.environ.get('DB_PORT', 3306)
db_name = os.environ.get('DB_NAME', 'call_center')
db_url = f'mysql+pymysql://{db_user}:{db_pwd}@{db_host}/{db_name}'

db = create_engine(db_url, echo=True)
metadata = MetaData()

table_users = Table('users', metadata, 
    Column('id', Integer, primary_key=True),
    Column('username', String(50), unique=True, nullable=False),
    Column('fio', String(200), nullable=False),
    Column('phone', String(11), nullable=False))

table_contacts = Table('contacts', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100), nullable=False),
    Column('phone', String(11), nullable=False),
    Column('orders', JSON, nullable=True))
