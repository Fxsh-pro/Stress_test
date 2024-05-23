import json
from io import BytesIO
from math import ceil

from flask import Blueprint, render_template, request, send_file, Response, flash, redirect, url_for
from flask_login import current_user, login_required

from app import db_operation

bp = Blueprint('testing', __name__, url_prefix='/testing')
MAX_PER_PAGE = 4


# create table test_configs
# (
#     id                int auto_increment
#         primary key,
#     endpoint          varchar(255)                                   not null,
#     request_body      text                                           null,
#     method            enum ('GET', 'POST', 'PUT', 'DELETE', 'PATCH') not null,
#     request_arguments text                                           null,
#     count_of_tests    int                                            not null,
#     headers           text                                           null,
#     user_id           int                                            not null,
#     created_at        datetime default CURRENT_TIMESTAMP             null,
#     constraint test_configs_ibfk_1
#         foreign key (user_id) references users (id)
#             on delete cascade
# );

@bp.route('/')
@db_operation
@login_required
def index(cursor):
    page = request.args.get('page', 1, type=int)
    user_id = current_user.get_id()
    is_admin = current_user.is_authenticated and current_user.is_admin()
    print(is_admin)
    print("HERE")

    base_query = ("SELECT id, endpoint, request_body, method, "
                  "request_arguments, count_of_tests, headers, created_at, user_id "
                  "FROM test_configs")
    count_query = "SELECT COUNT(*) as count FROM test_configs"

    if not is_admin:
        base_query += f" WHERE user_id = {user_id}"
        count_query += f" WHERE user_id = {user_id}"

    offset = (page - 1) * MAX_PER_PAGE
    paginated_query = base_query + " LIMIT %s OFFSET %s"
    cursor.execute(paginated_query, (MAX_PER_PAGE, offset))
    tests = cursor.fetchall()

    cursor.execute(count_query)
    total_tests = cursor.fetchone()[0]
    page_count = ceil(total_tests / MAX_PER_PAGE)
    pages = range(1, page_count + 1)

    return render_template("tests/index.html", data=tests, pages=pages, page=page, page_count=page_count)


@bp.route('/new', methods=['GET', 'POST'])
@db_operation
@login_required
# @check_for_privelege('create_test')
def create(cursor):
    if request.method == 'POST':
        endpoint = request.form['endpoint']
        method = request.form['method']
        request_arguments = request.form.get('request_arguments')
        count_of_tests = request.form['count_of_tests']
        headers = request.form.get('headers')
        request_body = request.form.get('request_body')
        user_id = current_user.get_id()

        query = (
            "INSERT INTO test_configs (endpoint, method, request_arguments, count_of_tests, request_body, headers, user_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)")
        cursor.execute(query, (endpoint, method, request_arguments, count_of_tests, request_body, headers, user_id))
        flash('Тест успешно создан!', 'success')
        return redirect(url_for('testing.index'))

    return render_template('tests/new_test.html')


@bp.route('/<int:test_id>/edit', methods=['GET', 'POST'])
@db_operation
@login_required
def update(cursor, test_id):
    if request.method == 'POST':
        endpoint = request.form['endpoint']
        method = request.form['method']
        request_arguments = request.form.get('request_arguments')
        count_of_tests = request.form['count_of_tests']
        headers = request.form.get('headers')
        request_body = request.form.get('request_body')

        print((endpoint, method, request_arguments, request_body, count_of_tests, headers, test_id))

        query = ("UPDATE test_configs SET endpoint=%s, method=%s, request_arguments=%s, request_body=%s, "
                 "count_of_tests=%s, headers=%s WHERE id=%s")
        cursor.execute(query, (endpoint, method, request_arguments, request_body, count_of_tests, headers, test_id))
        flash('Тест успешно обновлен!', 'success')
        return redirect(url_for('testing.index'))

    cursor.execute("SELECT * FROM test_configs WHERE id = %s", (test_id,))
    test = cursor.fetchone()
    return render_template('tests/edit_test.html', test=test)


@bp.route('/<int:test_id>/delete', methods=['POST'])
@db_operation
def delete(cursor, test_id):
    cursor.execute("DELETE FROM test_configs WHERE id = %s", (test_id,))
    flash('Тест успешно удален!', 'success')
    return redirect(url_for('testing.index'))


@bp.route('/<int:test_id>', methods=['GET'])
@db_operation
def view(cursor, test_id):
    cursor.execute("SELECT * FROM test_results where id = %s", (test_id,))
    test = cursor.fetchone()

    return render_template('tests/view.html', test=test)


# @bp.route('/<int:test_id>/delete', methods=['POST'])
# @db_operation
# def delete(cursor, test_id):
#     cursor.execute("DELETE FROM test_configs WHERE id = %s", (test_id,))
#     flash('Тест успешно удален!', 'success')
#     return redirect(url_for('testing.index'))


@bp.route('/results')
@db_operation
@login_required
def results(cursor):
    page = request.args.get('page', 1, type=int)
    user_id = current_user.get_id()
    is_admin = current_user.is_authenticated and current_user.is_admin()
    print(is_admin)
    print("HERE")

    base_query = ("SELECT tr.id, tr.test_id, tr.start_time, tr.end_time, tr.metrics, "
                  "tc.endpoint, tc.method, tc.user_id "
                  "FROM test_results tr "
                  "JOIN test_configs tc ON tr.test_id = tc.id")
    count_query = "SELECT COUNT(*) as count FROM test_results tr"

    if not is_admin:
        base_query += f" WHERE tc.user_id = {user_id}"
        count_query += f" WHERE tc.user_id = {user_id}"

    offset = (page - 1) * MAX_PER_PAGE
    paginated_query = base_query + " LIMIT %s OFFSET %s"

    cursor.execute(paginated_query, (MAX_PER_PAGE, offset))
    results = cursor.fetchall()
    print(results)
    dict_results = []
    for result in results:
        result_dict = result._asdict()
        result_dict['metrics'] = json.loads(result_dict['metrics'])
        dict_results.append(result_dict)

    cursor.execute(count_query)
    total_results = cursor.fetchone()[0]
    page_count = ceil(total_results / MAX_PER_PAGE)
    pages = range(1, page_count + 1)

    return render_template("tests/results.html", data=dict_results, pages=pages, page=page, page_count=page_count)
