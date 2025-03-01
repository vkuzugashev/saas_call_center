import sys, os, json
from flask import Flask, render_template, request, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from models import db, Calls, User
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

manager_user = os.environ.get('MANAGER_USER')
manager_pwd = os.environ.get('MANAGER_PWD')
db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PWD')
db_name = os.environ.get('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SECRET_KEY'] = 'secret-key-goes-here'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    print(f'Load user user_id={user_id}')
    if user_id == '1':
        return User(id=1, username=manager_user)
    else:
        return None

@app.route('/')
@login_required
def index():
#    if current_user.is_authenticated:
#      return redirect(url_for('profile'))
#    else:
    return render_template('holl.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User(id=1, username=manager_user, password=manager_pwd)        
        if user.username == username and user.password == password:
            print(user)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    else:
        return render_template('login.html')

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('profile'))
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         email = request.form['email']
#         user = User.query.filter_by(username=username).first()
#         if user:
#             flash('Username already taken')
#         else:
#             hashed_password = generate_password_hash(password)
#             new_user = User(username=username, password=hashed_password, email=email)
#             db.session.add(new_user)
#             db.session.commit()
#             flash('Account created successfully')
#             return redirect(url_for('login'))
#     return render_template('register.html')

# @app.route('/profile')
# def profile():
#     if current_user.is_authenticated:
#         return render_template('profile.html', user=current_user)
#     else:
#         return redirect(url_for('login'))

# @app.route('/logout')
# def logout():
#     logout_user()
#     return redirect(url_for('index'))

def connection_bd2(fromdt, todt):
    result = Calls.query.filter((Calls.call_start >= fromdt) & (Calls.call_start <= todt)).all()
    return result

   
def get_page(data, page_size, page_index):
    page_size = 15
    total_items = len(data)
    total_pages = (total_items + page_size - 1) // page_size
    start_index = (page_index - 1) * page_size
    end_index = page_index * page_size
    page_data = data[start_index:end_index]

    print(page_data)
    return page_data, total_pages

@app.route('/history', defaults={ 'page_index': 1, 'fromdt': '2024-01-01', 'todt': '2024-01-31' })
@app.route('/history/<fromdt>/<todt>/<int:page_index>', methods=['GET'])
@login_required
def history(fromdt, todt, page_index):
    print(fromdt, todt, page_index)
    data = connection_bd2(fromdt, todt)
    page_data, total_pages = get_page(data, 1, page_index)
    return render_template('history.html', data=page_data, total_pages=total_pages, fromdt=fromdt, todt=todt, page_index=page_index)

if __name__ == '__main__':
#    with app.app_context():
#        db.create_all()
    app.run(debug=True)

