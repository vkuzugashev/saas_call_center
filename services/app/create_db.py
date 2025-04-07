import os
from flask import Flask
from models import User, db
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Читаем переменные окружения
DB_DRIVER = os.getenv('DB_DRIVER', 'mysql')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PWD = os.getenv('DB_PWD')
DB_NAME = os.getenv('DB_NAME', 'call_center')
MANAGER_USER = os.getenv('MANAGER_USER')
MANAGER_PWD = os.getenv('MANAGER_PWD')

# Формируем строку подключения к базе данных
SQLALCHEMY_DATABASE_URI = f'{DB_DRIVER}+pymysql://{DB_USERNAME}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'

# Настраиваем приложение Flask
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализируем базу данных
db.init_app(app)

if __name__ == '__main__':
    # Операции с базой данных выполняются внутри контекста приложения
    with app.app_context():
         db.create_all()
         print('База данных создана успешно.')

         # Добавляем начальные данные для пользователя manager

         # Если пользователя менежер нет то создадим его и пароль по умолчанию
         manager = User.query.filter_by(username=MANAGER_USER).first()
         if manager is None:
            manager = User(
               department='admins',
               username=MANAGER_USER,
               fio='администратор',
               phone='00000000000'
            )
            manager.set_password(MANAGER_PWD)
            db.session.add(manager)

         db.session.commit()
         print('Начальные данные для пользователя manager добавлены.')