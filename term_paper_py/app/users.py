import mysql.connector as connector
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db_connector, db_operation
from auto import check_for_privelege

bp = Blueprint('users', __name__, url_prefix='/users')


def get_roles(cursor):
    cursor.execute("SELECT * FROM roles")
    return cursor.fetchall()


@bp.route('/')
@db_operation
def index(cursor):
    cursor.execute("SELECT users.*, roles.name AS role FROM users LEFT JOIN roles ON users.role_id = roles.id")
    users = cursor.fetchall()
    return render_template('users/index.html', users=users)


@bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@check_for_privelege('delete')
@db_operation
def delete(cursor, user_id):
    query = ("DELETE FROM users WHERE id = %s")
    cursor.execute(query, (user_id,))
    flash('Учетная запись успешно удалена', 'success')
    return redirect(url_for('users.index'))


@bp.route('/new', methods=['POST', 'GET'])
@login_required
@check_for_privelege('create')
@db_operation
def new(cursor):
    user_data = {}
    if request.method == 'POST':
        fields = ('login', 'password', 'first_name', 'middle_name', 'last_name', 'role_id')
        user_data = {field: request.form[field] or None for field in fields}
        try:
            query = (
                "INSERT INTO users (login, password_hash, first_name, middle_name, last_name, role_id) VALUES "
                "(%(login)s, SHA2(%(password)s, 256), %(first_name)s, %(middle_name)s, %(last_name)s, %(role_id)s)"
            )
            cursor.execute(query, user_data)
            print(cursor.statement)
            flash('Учетная запись успешно создана', 'success')
            return redirect(url_for('users.index'))
        except connector.errors.DatabaseError:
            flash('Произошла ошибка при создании записи. Проверьте, что все необходимые поля заполнены', 'danger')

    return render_template('users/new.html', user_data=user_data, roles=get_roles(cursor))


@bp.route('/<int:user_id>/view')
@check_for_privelege('read')
def view(user_id):
    user_data = {}
    with db_connector.connect().cursor(named_tuple=True, buffered=True) as cursor:
        query = ("SELECT * FROM users WHERE id = %s")
        cursor.execute(query, [user_id])
        user_data = cursor.fetchone()
        if user_data is None:
            flash('Пользователя нет в базе данных', 'danger')
            return redirect(url_for('users.index'))
        query = "SELECT name FROM roles WHERE id = %s"
        cursor.execute(query, [user_data.role_id])
        user_role = cursor.fetchone()
        return render_template('users/view.html', user_data=user_data, user_role=user_role.name)


@bp.route('/<int:user_id>/edit', methods=['POST', 'GET'])
@login_required
@check_for_privelege('update')
@db_operation
def edit(cursor, user_id):
    query = ("SELECT first_name, middle_name, last_name, role_id "
             "FROM users WHERE id = %s")
    cursor.execute(query, [user_id])
    user_data = cursor.fetchone()
    if user_data is None:
        flash('Пользователя нет в базе данных', 'danger')
        return redirect(url_for('users'))

    if request.method == 'POST':
        fields = ['first_name', 'middle_name', 'last_name', 'role_id']
        if not current_user.can('assign_role'):
            fields.remove('role_id')
        user_data = {field: request.form[field] or None for field in fields}
        user_data['id'] = user_id
        try:
            field_assignments = ', '.join([f"{field} = %({field})s" for field in fields])
            query = (f"UPDATE users SET {field_assignments} "
                     "WHERE id = %(id)s")
            cursor.execute(query, user_data)
            flash('Учетная запись успешно изменена', 'success')
            return redirect(url_for('users.index'))
        except connector.errors.DatabaseError as error:
            flash(f'Произошла ошибка при изменении записи: {error}', 'danger')
    return render_template('users/edit.html', user_data=user_data, roles=get_roles(cursor))
