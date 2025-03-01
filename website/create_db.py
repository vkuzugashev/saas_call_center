import os
from flask import Flask
from models import User, db
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

db_user = os.environ.get('DB_USER', 'root')
db_pwd = os.environ.get('DB_PWD', '1234567')
db_host = os.environ.get('DB_HOST', 'localhost')
db_port = os.environ.get('DB_PORT', 3306)
db_name = os.environ.get('DB_NAME', 'call_center')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pwd}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        print('Создана база данных users')