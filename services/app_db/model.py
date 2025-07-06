import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Boolean, String, Integer, Column, DateTime, Text, JSON

load_dotenv()

db_user = os.environ.get('DB_USERNAME', 'root')
db_pwd = os.environ.get('DB_PWD', '1234567')
db_host = os.environ.get('DB_HOST', 'localhost')
db_port = os.environ.get('DB_PORT', 3306)
db_name = os.environ.get('DB_NAME', 'call_center')
db_url = f'mysql+pymysql://{db_user}:{db_pwd}@{db_host}/{db_name}'
db = create_engine(db_url, echo=True)

metadata = MetaData()

table_calls = Table('calls', metadata, 
    Column('id', Integer, primary_key=True, autoincrement='auto'),
    Column('caller', String(20), nullable=False),
    Column('callee', String(20),  nullable=False),
    Column('call_start', DateTime, nullable=False),
    Column('call_end', DateTime, nullable=True),
    Column('call_status', String(50), nullable=True),
    Column('record_file', String(255), nullable=True),
    Column('transcription_id', String(255), nullable=True),
    Column('transcription_status', Integer, nullable=False, default=0),
    Column('transcription', Text, nullable=True),
    Column('dialog', Text, nullable=True)
)

table_users = Table('users', metadata, 
    Column('id', Integer, primary_key=True),
    Column('username', String(50), unique=True, nullable=False),
    Column('fio', String(200), nullable=False),
    Column('phone', String(11), nullable=False))

table_contacts = Table('contacts', metadata,
    Column('id', Integer, primary_key=True, autoincrement='auto'),
    Column('name', String(100), nullable=False),
    Column('phone', String(11), nullable=False),
    Column('orders', JSON, nullable=True),
    Column('call_date', DateTime, nullable=True),
    Column('is_lead', Boolean, nullable=False, default=True),
    Column('note',  Text, nullable=True),
    Column('updated_at', DateTime, nullable=True)   
)

