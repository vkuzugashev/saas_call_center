
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from models import db, CallCategory


categories_bp = Blueprint('categories_bp', __name__, template_folder='templates/call_categories')

@categories_bp.route('/call_categories', methods=['GET', 'POST'])
@login_required
def call_categories():
    categories = CallCategory.query.all()

    if request.method == 'POST':
        # Обработка формы для добавления новой категории
        name = request.form['name']

        new_category = CallCategory(name=name)
        db.session.add(new_category)
        db.session.commit()
        flash('Категория успешно добавлена!', 'success')
        return redirect(url_for('categories_bp.call_categories'))

    return render_template('call_categories.html', categories=categories)

@categories_bp.route('/call_categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_call_category(id):
    category = CallCategory.query.get_or_404(id)

    if request.method == 'POST':
        # Обработка формы для редактирования категории
        category.name = request.form['name']
        db.session.commit()
        flash('Категория успешно отредактирована!', 'success')
        return redirect(url_for('categories_bp.call_categories'))

    return render_template('edit_call_category.html', category=category)

@categories_bp.route('/call_categories/delete/<int:id>', methods=['GET'])
@login_required
def delete_call_category_confirmation(id):
    category = CallCategory.query.get_or_404(id)
    return render_template('delete_confirmation.html', category=category)


@categories_bp.route('/call_categories/delete/<int:id>', methods=['POST'])
@login_required
def delete_call_category(id):
    category = CallCategory.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('Категория успешно удалена!', 'success')
    return redirect(url_for('categories_bp.call_categories'))