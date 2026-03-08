from datetime import datetime, timezone
import os
from typing import Optional
from flask_login import UserMixin
from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, SmallInteger, String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
from dotenv import load_dotenv

load_dotenv()

DB_DRIVER = os.getenv('DB_DRIVER')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER')
DB_PWD = os.getenv('DB_PWD')
DB_NAME = os.getenv('DB_NAME')
MANAGER_USER = os.getenv('APP_MANAGER_USER')
MANAGER_PWD = os.getenv('APP_MANAGER_PWD')

# Формируем строку подключения к базе данных
DATABASE_URI = f'{DB_DRIVER}+pymysql://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'

engine = create_engine(DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    __abstract__ = True
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,        
        default=func.now(),         # Устанавливаем текущее время по умолчанию        
        onupdate=func.now()         # Обновляем время при каждом обновлении записи        
    )

class User(Base, UserMixin):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    department: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(50), unique=True)
    fio: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(11))
    queue: Mapped[Optional[str]] = mapped_column(String(100))
    # Хранится хеш пароля   
    password_hash: Mapped[str] = mapped_column(String(256), use_existing_column=True)  # Хранится хеш пароля    
    asterisk_hash: Mapped[str] = mapped_column(String(256), use_existing_column=True)  # Хранится хеш пароля для asterisk

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        # создать md5 пароль для asterisk
        self.asterisk_hash = hashlib.md5(f'{self.username}:asterisk:{password}'.encode()).hexdigest()

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Call(Base):
    __tablename__ = 'calls'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    caller: Mapped[str] = mapped_column(String(11))
    callee: Mapped[str] = mapped_column(String(11))
    call_start: Mapped[datetime]
    call_end: Mapped[Optional[datetime]]
    call_status: Mapped[str] = mapped_column(String(12))
    record_file: Mapped[Optional[str]] = mapped_column(String(255))
    transcription_id: Mapped[Optional[str]] = mapped_column(String(255))
    transcription_status: Mapped[int] = mapped_column(default=0)
    transcription: Mapped[Optional[str]] = mapped_column(Text)
    dialog: Mapped[Optional[str]] = mapped_column(Text)
    
    def __repr__(self):
        return f'<Call {self.caller} -> {self.callee}>'


class Contact(Base):
    __tablename__ = 'contacts'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(11))
    call_date: Mapped[Optional[datetime]]
    is_lead: Mapped[bool] = mapped_column(default=True)
    note: Mapped[Optional[str]] = mapped_column(Text)
    orders: Mapped[Optional[dict]] = mapped_column(JSON)

    def __repr__(self):
        return f'<Contact {self.name}>'


class CallCategory(Base):
    __tablename__ = 'call_categories'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    def __repr__(self):
        return f'<CallCategory {self.name}>'


class PJSIPEndpoint(Base):
    __tablename__ = "ps_endpoints"
    
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    transport: Mapped[str] = mapped_column(String(80))
    aors: Mapped[str] = mapped_column(String(80))
    auth: Mapped[str] = mapped_column(String(80))
    context: Mapped[str] = mapped_column(String(80))
    direct_media: Mapped[str] = mapped_column(String(80))
    disallow: Mapped[str] = mapped_column(String(80))
    allow: Mapped[str] = mapped_column(String(80))

    def __repr__(self):
        return f'<PJSIPEndpoint {self.transport}>' ,

# Таблица pjsip_aors
class PJSIPEndpointAOR(Base):
    __tablename__ = 'ps_aors'
    
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    max_contacts: Mapped[int] = mapped_column(default=1)
    remove_existing: Mapped[bool] = mapped_column(default=True)


# Таблица pjsip_authentications
class PJSIPAuthentication(Base):
    __tablename__ = 'ps_auths'
    
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    username: Mapped[str] = mapped_column(String(80))
    auth_type: Mapped[str] = mapped_column(String(80))
    password: Mapped[str] = mapped_column(String(80))
    md5_cred: Mapped[str] = mapped_column(String(80))


# Таблица pjsip_transports
class PJSIPTransport(Base):
    __tablename__ = 'ps_transports'
    
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    protocol: Mapped[str] = mapped_column(String(10))   #Enum('tcp', 'udp', 'tls'))
    bind_addr: Mapped[str] = mapped_column(String(80))
    port: Mapped[int]
    certfile: Mapped[str] = mapped_column(String(255))
    privkeyfile: Mapped[str] = mapped_column(String(255))


class Extension(Base):
    """
    Представляет таблицу `extensions`, содержащую информацию о расширениях (extens).
    """
    __tablename__ = 'extensions'

    # Основные поля таблицы
    id: Mapped[int] = mapped_column(primary_key=True)
    exten: Mapped[str] = mapped_column(String(10))  # Номер телефона
    context: Mapped[str] = mapped_column(String(80))  # Контекст набора
    priority: Mapped[int] = mapped_column(SmallInteger)  # Уровень приоритета
    app: Mapped[str] = mapped_column(String(80))  # Приложение обработки звонка
    appdata: Mapped[str] = mapped_column(Text)  # Дополнительные настройки приложения
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # Активно ли расширение
    description: Mapped[Optional[str]] = mapped_column(Text)  # Описание расширения


def init_db():
    """Создаёт таблицы и инициализирует начальные данные."""
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы.")

    # Используем контекст сессии
    with Session(engine) as session:
        # Если пользователя менежер нет то создадим его и пароль по умолчанию
        user = session.execute(
            select(User).where(User.username == MANAGER_USER)
        ).scalar_one_or_none()

        if not user:
            manager = User(
                department='admins',
                username=MANAGER_USER,
                fio='администратор',
                phone='0000'
            )
            manager.set_password(MANAGER_PWD)
            session.add(manager)
            session.commit()
            print('Начальные данные для пользователя manager добавлены.')        

def get_db():
    """Генератор сессии — для Flask или FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

