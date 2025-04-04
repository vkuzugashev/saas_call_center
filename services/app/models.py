from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(100))
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

class Calls(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement='auto')
    caller = db.Column(db.String(20), nullable=False)
    callee = db.Column(db.String(20), nullable=False)
    caller_id = db.Column(db.String(200), nullable=True)
    callee_id = db.Column(db.String(200), nullable=True)
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
    
class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement='auto')
    greeting_file = db.Column(db.String(255), nullable=True)
    modules = db.Column(db.JSON, nullable=False, default={})

    def __repr__(self):
        return f'<Settings>'

class CallCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<CallCategory {self.name}>'
