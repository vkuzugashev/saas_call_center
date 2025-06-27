from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    fio = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(11), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # Хранится хеш пароля    
    asterisk_hash = db.Column(db.String(256), nullable=False)  # Хранится хеш пароля для asterisk
    queue = db.Column(db.String(100), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)    

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        # создать md5 пароль для asterisk
        self.asterisk_hash = hashlib.md5(f'{self.username}:asterisk:{password}'.encode()).hexdigest()

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Call(db.Model):
    __tablename__ = 'calls'
    id = db.Column(db.Integer, primary_key=True)
    caller = db.Column(db.String(11), nullable=False)
    callee = db.Column(db.String(11), nullable=False)
    call_start = db.Column(db.DateTime, nullable=False)
    call_end = db.Column(db.DateTime, nullable=True)
    call_status = db.Column(db.String(12), nullable=False)
    record_file = db.Column(db.String(255), nullable=True)
    transcription_id = db.Column(db.String(255), nullable=True)
    transcription_status = db.Column(db.Integer, nullable=False, default=0)
    transcription = db.Column(db.Text, nullable=True)
    dialog = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Call {self.caller} -> {self.callee}>'

class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(11), nullable=False)
    call_date = db.Column(db.DateTime, nullable=True)
    is_lead = db.Column(db.Boolean, nullable=False, default=True)
    note = db.Column(db.Text, nullable=True)
    orders = db.Column(db.JSON, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)   

    def __repr__(self):
        return f'<Contact {self.name}>'


class CallCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<CallCategory {self.name}>'
    

