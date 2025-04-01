import os
from flask import Flask
from models import User, Settings, db
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Читаем переменные окружения
DB_DRIVER = os.getenv('DB_DRIVER', 'mysql')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USERNAME = os.getenv('DB_USERNAME', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'call_center')

# Формируем строку подключения к базе данных
SQLALCHEMY_DATABASE_URI = f'{DB_DRIVER}+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'

# Настраиваем приложение Flask
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализируем базу данных
db.init_app(app)

if __name__ == '__main__':
    # Операции с базой данных выполняются внутри контекста приложения
    with app.app_context():
        # Удаляем и создаем заново базу данных
        #db.drop_all()
        db.create_all()
        print('База данных создана успешно.')

        # Добавляем начальные данные для пользователя manager
        manager = User(
            department='admins',
            username=os.getenv('MANAGER_USER', 'manager'),
            fio='администратор',
            phone='00000000000'
        )
        password=os.getenv('MANAGER_PWD', 'password')
        manager.set_password(password)
        db.session.add(manager)

        settings = Settings(
            greeting_file = "",
            modules = { "module-speech" : False }
        )
        db.session.add(settings)
        
        db.session.commit()
        print('Начальные данные для пользователя manager добавлены.')