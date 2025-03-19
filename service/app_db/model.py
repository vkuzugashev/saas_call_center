import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, String, Integer, Column, DateTime, Text

load_dotenv()

db_user = os.environ.get('DB_USER', 'root')
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
    Column('caller_id', String(100), nullable=True),
    Column('callee_id', String(100), nullable=True),
    Column('call_start', DateTime, nullable=False),
    Column('call_end', DateTime, nullable=True),
    Column('call_status', String(50), nullable=True),
    Column('record_file', String(255), nullable=True),
    Column('transcription_id', String(255), nullable=True),
    Column('transcription_status', Integer, nullable=False, default=0),
    Column('transcription', Text, nullable=True)
)

if __name__ == '__main__':
    metadata.drop_all(db)
    metadata.create_all(db)
    print('Database schema created.')
