from flask import Blueprint, current_app, render_template, send_file
from flask_login import login_required
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from sqlalchemy import select
from models.model import get_db, User, Call

report_bp = Blueprint('report_bp', __name__, template_folder='../templates/report')

def get_session():
    return next(get_db())

@report_bp.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    """
    Обработчик для отображения отчета по звонкам.

    Returns:
        Response: Ответ сервера.
    """
    # Получаем данные за последний месяц
    start_date = datetime.now() - timedelta(days=30)
    
    with get_session() as session:
        calls = session.query(Call).filter(Call.call_start >= start_date).all()

        # Группируем данные по звонящему и отделу
        callees = {}
        departments = {}
        unknown_department_name = 'Не определен'
        
        for call in calls:
            callee = session.query(User).filter(User.username == call.callee).first()            
            if callee is None:
                continue
            
            if callee not in callees:
                callees[callee] = {'count': 0, 'duration': timedelta()}
            
            callees[callee]['count'] += 1
            
            if call.call_end:
                callees[callee]['duration'] += call.call_end - call.call_start

            if callee.department is None:
                department_name = unknown_department_name
            else:
                department_name = callee.department        
            
            if department_name not in departments:
                departments[department_name] = {'count': 0, 'duration': timedelta()}
            
            departments[department_name]['count'] += 1

            if call.call_end:
                departments[department_name]['duration'] += call.call_end - call.call_start

    return render_template('report.html', callees=callees, departments=departments, modules = current_app.config['modules'])

@report_bp.route('/report/download', methods=['GET'])
@login_required
def download_report():
    """
    Обработчик для выгрузки отчета по звонкам в Excel.

    Returns:
        Response: Ответ сервера.
    """
    # Получаем данные за последний месяц
    start_date = datetime.now() - timedelta(days=30)
    
    with get_session() as session:
        calls = session.query(Call).filter(Call.call_start >= start_date).all()

        # Группируем данные по звонящему и отделу
        callers = {}
        departments = {}
        
        for call in calls:
            caller = session.query(User).filter(User.username == call.caller).first()
        
            if caller not in callers:
                callers[caller] = {'count': 0, 'duration': timedelta()}

            callers[caller]['count'] += 1
        
            if call.call_end:
                callers[caller]['duration'] += call.call_end - call.call_start

            if caller.department not in departments:
                departments[caller.department] = {'count': 0, 'duration': timedelta()}

            departments[caller.department]['count'] += 1
        
            if call.call_end:
                departments[caller.department]['duration'] += call.call_end - call.call_start

        # Создаем DataFrame для звонков
        callers_df = pd.DataFrame.from_dict(callers, orient='index')
        callers_df['username'] = callers_df.index.map(lambda x: x.username)
        callers_df['department'] = callers_df.index.map(lambda x: x.department)
        callers_df.reset_index(drop=True, inplace=True)

        # Создаем DataFrame для отделов
        departments_df = pd.DataFrame.from_dict(departments, orient='index')
        departments_df.reset_index(inplace=True)
        departments_df.columns = ['department', 'count', 'duration']

        # Сохраняем DataFrame в Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            callers_df.to_excel(writer, sheet_name='Callers', index=False)
            departments_df.to_excel(writer, sheet_name='Departments', index=False)

        output.seek(0)

    return send_file(output, download_name='report.xlsx', as_attachment=True)
