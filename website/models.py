from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'
    
class Calls(db.Model):
    #__tablename__ = 'calls'
    id = db.Column(db.Integer, primary_key=True, autoincrement='auto')
    caller = db.Column(db.String(20), nullable=False)
    callee = db.Column(db.String(20), nullable=False)
    caller_id = db.Column(db.String(200), nullable=True)
    callee_id = db.Column(db.String(200),  nullable=True)
    call_start = db.Column(db.String(200), nullable=False)
    call_end = db.Column(db.String(200), nullable=True)
    call_status = db.Column(db.String(200), nullable=False)
    record_file = db.Column(db.String(255), nullable=True)

# table_calls = Table('calls', metadata, 
#     Column('id', Integer, primary_key=True, autoincrement='auto'),
#     Column('caller', String(20), nullable=False),
#     Column('callee', String(20),  nullable=False),
#     Column('caller_id', String(100), nullable=True),
#     Column('callee_id', String(100), nullable=True),
#     Column('call_start', DateTime, nullable=False),
#     Column('call_end', DateTime, nullable=True),
#     Column('call_status', String(50), nullable=True),
#     Column('record_file', String(255), nullable=True)