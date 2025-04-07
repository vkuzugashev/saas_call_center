import csv
from datetime import datetime
import io
import logging
from operator import or_
import os
import tempfile
from flask import Blueprint, flash, make_response, redirect, render_template, request, url_for
from flask_login import login_required

from models import db, Contact


logger = logging.getLogger("users")
contacts_bp = Blueprint('contacts_bp', __name__, template_folder='../templates/contacts')

# показать все контакты с фильтром по номеру телефона
@contacts_bp.route('/contacts')
@login_required
def contacts():
   search = request.args.get('search')
   if search:
       contacts = Contact.query.filter(
           or_(
               Contact.phone.like(f'%{search}%'),
               Contact.name.like(f'%{search}%')
           )
       ).all()
   else:
       contacts = Contact.query.all()
   return render_template('contacts.html', contacts=contacts, search=search)

@contacts_bp.route('/contacts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact(id):
   contact = Contact.query.get_or_404(id)
   if request.method == 'POST':
       contact.name = request.form.get('name')
       contact.phone = request.form.get('phone')
       call_date = request.form.get('call_date')
       if call_date:
           contact.call_date = datetime.strptime(call_date, '%Y-%m-%d %H:%M:%S')
       else:
           contact.call_date = None
       contact.is_lead = request.form.get('is_lead') == 'True'
       contact.note = request.form.get('note')
       contact.orders = request.form.get('orders')
       db.session.commit()
       flash('Контакт успешно обновлен!', 'success')
       return redirect(url_for('contacts_bp.contacts'))
   return render_template('edit_contact.html', contact=contact)


@contacts_bp.route('/contacts/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_contact(id):
   contact = Contact.query.get_or_404(id)
   if request.method == 'POST':
       db.session.delete(contact)
       db.session.commit()
       flash('Контакт успешно удален!', 'success')
       return redirect(url_for('contacts_bp.contacts'))
   return render_template('delete_contact.html', contact=contact)

@contacts_bp.route('/contacts/download', methods=['GET'])
@login_required
def download_contacts():
   contacts = Contact.query.all()
   si = io.StringIO()
   writer = csv.writer(si)
   writer.writerow(['name', 'phone', 'call_date', 'is_lead', 'note', 'orders'])
   for contact in contacts:
       writer.writerow([
           contact.name,
           contact.phone,
           contact.call_date.strftime('%Y-%m-%d %H:%M:%S') if contact.call_date else '',
           contact.is_lead,
           contact.note,
           contact.orders
       ])
   # Преобразуем содержимое StringIO в байты
   output = make_response(si.getvalue())
      
   # Устанавливаем заголовок Content-Disposition для скачивания файла
   output.headers["Content-Disposition"] = "attachment; filename=contacts.csv"
   output.headers["Content-type"] = "text/csv"

   return output

@contacts_bp.route('/contacts/upload', methods=['GET', 'POST'])
@login_required
def upload_contacts():
   if request.method == 'POST':
       # Проверяем, есть ли файл в запросе
       if 'file' not in request.files:
           flash('Нет файла для загрузки', 'warning')
           return redirect(request.url)
       
       file = request.files['file']

       # Если пользователь не выбрал файл
       if file.filename == '':
           flash('Не выбран файл', 'warning')
           return redirect(request.url)      

       # Проверяем расширение файла
       if not file.filename.lower().endswith('.csv'):
           logger.warning(f'Загружен файл контактов с неправильным расширением: {file.filename}')
           flash('Поддерживаются только CSV-файлы','warning')
           return redirect(request.url)

       # Получаем путь к временному файлу
       filepath = os.path.join(tempfile.gettempdir(), file.filename)
       file.save(filepath)
       logger.info(f'загружен файл пользователей: {filepath}')
       # получаем текущую дату и время для записи времени обновления без милисекунд
       upload_time = datetime.now().replace(microsecond=0)       
       # Открываем временный файл и загружаем данные в базу данных
       with open(filepath, 'r', encoding='utf-8') as csv_file:
           reader = csv.reader(csv_file)
           next(reader)  # Пропускаем первую строку (заголовки)
           for row in reader:
               try:
                   name, phone, _, is_lead, note, orders = row
               except ValueError:
                   continue  # Пропускаем строки с неверной структурой
               contact = Contact.query.filter_by(name=name, phone=phone).first()
               if contact:
                   contact.orders = orders
                   contact.updated_at = upload_time
               else:
                   contact = Contact(
                       name=name,
                       phone=phone,
                       is_lead=is_lead == 'True',
                       note=note,
                       orders=orders,
                       updated_at=upload_time
                   )
                   db.session.add(contact)
           
           db.session.commit()
           
           # Удалим все записи старше upload_time
           Contact.query.filter(Contact.updated_at < upload_time).delete() 
           db.session.commit()

           flash('Контакты успешно загружены!', 'success')    
           
       # удалим файл           
       os.remove(filepath)
       return redirect(url_for('contacts_bp.contacts'))
   else:
       return render_template('upload_contacts.html')

