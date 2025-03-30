
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from models import db, CallCategory

categories_bp = Blueprint('categories_bp', __name__, template_folder='../templates/call_categories')

@categories_bp.route('/call_categories', methods=['GET', 'POST'])
@login_required
def call_categories():
   """
   Обработчик для отображения и добавления категорий вызовов.

   Returns:
       Response: Ответ сервера.
   """
   categories = CallCategory.query.all()

   if request.method == 'POST':
       # Обработка формы для добавления новой категории
       name = request.form.get('name')

       if not name:
           flash('Имя категории не может быть пустым.', 'danger')
           return redirect(url_for('categories_bp.call_categories'))

       new_category = CallCategory(name=name)
       db.session.add(new_category)
       db.session.commit()
       flash(f'Категория [{name}] успешно добавлена!', 'success')
       return redirect(url_for('categories_bp.call_categories'))

   return render_template('call_categories.html', categories=categories)


@categories_bp.route('/call_categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_call_category(id):
   """
   Обработчик для редактирования категории вызова.

   Args:
       id (int): Идентификатор категории вызова, которую нужно редактировать.

   Returns:
       Response: Ответ сервера.
   """
   category = CallCategory.query.get_or_404(id)

   if request.method == 'POST':
       # Обработка формы для редактирования категории
       name = request.form.get('name')

       if not name:
           flash('Имя категории не может быть пустым.', 'danger')
           return redirect(url_for('categories_bp.edit_call_category', id=id))

       category.name = name
       db.session.commit()
       flash(f'Категория [{category.name}] успешно отредактирована!', 'success')
       return redirect(url_for('categories_bp.call_categories'))

   return render_template('edit_call_category.html', category=category)


@categories_bp.route('/call_categories/delete/<int:id>', methods=['GET'])
@login_required
def delete_call_category_confirmation(id):
   """
   Обработчик для отображения страницы подтверждения удаления категории вызова.

   Args:
       id (int): Идентификатор категории вызова, которую нужно удалить.

   Returns:
       Response: Ответ сервера.
   """
   category = CallCategory.query.get_or_404(id)
   return render_template('delete_confirmation.html', category=category)



@categories_bp.route('/call_categories/delete/<int:id>', methods=['POST'])
@login_required
def delete_call_category(id):
   """
   Обработчик для удаления категории вызова.

   Args:
       id (int): Идентификатор категории вызова, которую нужно удалить.

   Returns:
       Response: Ответ сервера.
   """
   category = CallCategory.query.get_or_404(id)
   db.session.delete(category)
   db.session.commit()
   flash(f'Категория [{category.name}] успешно удалена!', 'success')
   return redirect(url_for('categories_bp.call_categories'))
