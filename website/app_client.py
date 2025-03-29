import os
from dotenv import load_dotenv
import logging
from flask import (
    Flask, request, render_template, redirect, url_for, flash, send_file, abort,  make_response
)
from flask_login import (
    LoginManager, current_user, login_user, logout_user, login_required
)
import requests
from datetime import datetime, timedelta
from settings import settings_bp
from call_categories import categories_bp
from users import users_bp

# Импортируем модели из models.py
from models import db, User, Calls

load_dotenv()

# Уровень логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
# Настройка логирования
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("app_client")

# Читаем переменные из .env
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT'))  # Порт преобразуем в целое число
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Url для загрузки файла записи
RECORD_URL = os.getenv('RECORD_URL')

# Формируем URI для SQLAlchemy
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализируем DB
db.init_app(app)

# Инициализируем LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('holl.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user is not None and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))

        flash('Неправильное имя пользователя или пароль.')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        fio = request.form['fio']
        phone = request.form['phone']

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Имя пользователя уже занято.')
            return redirect(url_for('register'))

        new_user = User(
            username=username,
            fio=fio,
            phone=phone
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Аккаунт успешно создан!')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route("/record/<int:id>")
@login_required
def get_record_file(id):
    # Получаем звонок
    call = Calls.query.get_or_404(id)
    
    if call.record_file:
        file_url = RECORD_URL+'/'+call.record_file
        logger.debug(f'Начало загрузки файла: {file_url}')
        # Загрузка файла по ссылке
        response = requests.get(file_url, stream=True)
    
        # Проверяем успешность загрузки
        if response.status_code == 200:
            # Передача файла клиенту
            filename = os.path.basename(file_url)
            logger.debug(f'Загружен файл: {filename}')
            return send_file(response.raw, download_name=filename, as_attachment=True)
        else:
            return f"Не удалось загрузить файл. Код статуса: {response.status_code}", 500
    else:
        abort(404)

@app.route('/calls/log')
@login_required
def calls_log():
    # Установка значений by default
    date_time_format = '%Y-%m-%d'   # формат DD.MM.YY
    limit = 10
    today = datetime.now().strftime(date_time_format)  # Текущая дата в формате DD.MM.YYYY
    page = int(request.args.get('page', 1))
    fromdt = request.args.get('fromdt', today)
    todt = request.args.get('todt', today)

    # Преобразование строковых значений в объекты datetime
    try:
        from_date = datetime.strptime(fromdt, date_time_format)
        to_date = datetime.strptime(todt, date_time_format) + timedelta(days=1)
        
    except ValueError:
        # Если дата некорректна, возвращаем ошибку
        flash(f'Некорректный формат даты. Должен быть YYYY-MM-DD.')
        return redirect(url_for('calls_log'))

    # Определяем базовый запрос
    base_query = Calls.query.order_by(Calls.call_start)

    # Применяем фильтры по дате
    if from_date:
        base_query = base_query.filter(Calls.call_start >= from_date)
    if to_date:
        base_query = base_query.filter(Calls.call_start <= to_date)
  
    # Извлекаем записи для текущей страницы
    paginate = base_query.paginate(page=page, per_page=limit, error_out=False)

    # Формируем контекст для рендеринга
    context = {
        'pagination': paginate,
        'fromdt': fromdt,
        'todt': todt
    }

    return render_template('calls_log.html', **context)

app.register_blueprint(settings_bp)
app.register_blueprint(users_bp)
app.register_blueprint(categories_bp)

if __name__ == '__main__':
    app.run(debug=True)