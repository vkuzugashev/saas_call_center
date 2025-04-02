
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
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

        # Проверка наличия имени категории
        if not name:
            flash('Имя категории не может быть пустым.', 'danger')
            return redirect(url_for('categories_bp.call_categories'))
        
        # Проверка, что категория с таким именем не существует
        existing_category = CallCategory.query.filter_by(name=name).first()
        if existing_category:
            flash(f'Категория [{name}] уже существует.', 'danger')
            return redirect(url_for('categories_bp.call_categories'))
       
        # Создание новой категории вызова
        new_category = CallCategory(name=name)
        db.session.add(new_category)
        db.session.commit()
        flash(f'Категория [{name}] успешно добавлена!', 'success')
        return redirect(url_for('categories_bp.call_categories'))

    return render_template('call_categories.html', categories = categories, modules = current_app.config['modules'])


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
        newid = int(request.form.get('newid', 0))
        name = request.form.get('name')
        
        # Проверка наличия идентификатора категории
        if not newid:
            flash('Идентификатор категории не может быть пустым.', 'danger')
            return redirect(url_for('categories_bp.edit_call_category', id=id))
        
        if id != newid:
            # Проверка наличия дубликтов категории с таким же id
            existing_category = CallCategory.query.filter_by(id=newid).first()
            if existing_category:
                flash(f'Категория [{existing_category.name}] уже существует с таким id [{newid}].', 'danger')
                return redirect(url_for('categories_bp.edit_call_category', id=id))
            
        # Проверка наличия имени категории
        if not name:
            flash('Имя категории не может быть пустым.', 'danger')
            return redirect(url_for('categories_bp.edit_call_category', id=id))

        if id == newid:
            # Проверка наличия дубликтов категории с таким же именем
            existing_category = CallCategory.query.filter_by(name=name).first()
            if existing_category:
                flash(f'Категория [{name}] уже существует.', 'danger')
                return redirect(url_for('categories_bp.edit_call_category', id=id))
       
        category.id = newid
        category.name = name
        db.session.commit()
        flash(f'Категория [{category.name}] успешно отредактирована!', 'success')
        return redirect(url_for('categories_bp.call_categories'))

    return render_template('edit_call_category.html', category = category, modules = current_app.config['modules'])


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
   return render_template('delete_confirmation.html', category=category, modules = current_app.config['modules'])



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
