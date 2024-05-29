import csv
import json
from io import BytesIO, StringIO
from math import ceil

from flask import Blueprint, render_template, request, send_file, Response, flash, redirect, url_for
from flask_login import current_user, login_required

from app import db_operation

bp = Blueprint('testing', __name__, url_prefix='/testing')
MAX_PER_PAGE = 7


@bp.route('/')
@db_operation
@login_required
def index(cursor):
    page = request.args.get('page', 1, type=int)
    user_id = current_user.get_id()
    is_admin = current_user.is_authenticated and current_user.is_admin()

    base_query = ("SELECT id, endpoint, request_body, method, "
                  "request_arguments, count_of_tests, headers, created_at, user_id, was_tested "
                  "FROM test_configs "
                  "WHERE was_deleted = false ")
    count_query = "SELECT COUNT(*) as count FROM test_configs WHERE was_deleted = false "

    if not is_admin:
        base_query += f" AND user_id = {user_id}"
        count_query += f" AND user_id = {user_id}"

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
        user_id = current_user.get_id()

        query = (
            "INSERT INTO test_configs (endpoint, method, request_arguments, count_of_tests, request_body, headers, user_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)")
        cursor.execute(query, (endpoint, method, request_arguments, count_of_tests, request_body, headers, user_id))

        flash('Тест успешно обновлен!', 'success')
        return redirect(url_for('testing.index'))

    cursor.execute("SELECT * FROM test_configs WHERE id = %s", (test_id,))
    test = cursor.fetchone()
    return render_template('tests/edit_test.html', test=test)


@bp.route('/<int:test_id>/delete', methods=['POST'])
@db_operation
def delete(cursor, test_id):
    cursor.execute("UPDATE test_configs SET was_deleted = true WHERE id = %s", (test_id,))
    flash('Тест успешно удален!', 'success')
    return redirect(url_for('testing.index'))


@bp.route('/<int:test_id>', methods=['GET'])
@db_operation
def view(cursor, test_id):
    cursor.execute("SELECT * FROM test_configs where id = %s", (test_id,))
    test = cursor.fetchone()

    return render_template('tests/view.html', test=test)


@bp.route('/results')
@db_operation
@login_required
def results(cursor):
    page = request.args.get('page', 1, type=int)
    user_id = current_user.get_id()
    is_admin = current_user.is_authenticated and current_user.is_admin()

    base_query = ("SELECT tr.id, tr.test_id, tr.start_time, tr.end_time, tr.metrics, "
                  "tc.endpoint, tc.method, tc.user_id "
                  "FROM test_results tr "
                  "JOIN test_configs tc ON tr.test_id = tc.id")
    count_query = "SELECT COUNT(*) as count FROM test_results tr "

    if not is_admin:
        base_query += f" WHERE tc.user_id = {user_id}"
        count_query += f" JOIN test_configs tc ON tc.id = tr.test_id WHERE tc.user_id = {user_id}"

    offset = (page - 1) * MAX_PER_PAGE
    paginated_query = base_query + " LIMIT %s OFFSET %s"

    cursor.execute(paginated_query, (MAX_PER_PAGE, offset))
    results = cursor.fetchall()
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


@bp.route('/<int:test_id>/details', methods=['GET'])
@db_operation
def view_result_details(cursor, test_id):
    cursor.execute("SELECT * FROM test_results WHERE test_id = %s", (test_id,))
    test_result = cursor.fetchone()

    if test_result:
        result_dict = test_result._asdict()
        metrics = json.loads(result_dict['metrics'])
        result_dict['metrics'] = metrics
        return render_template('tests/result_detail.html', test_result=result_dict)

    flash('Test result not found!', 'error')
    return redirect(url_for('testing.index'))


@bp.route('/results_export.csv')
@db_operation
@login_required
def results_export(cursor):
    user_id = current_user.get_id()
    is_admin = current_user.is_authenticated and current_user.is_admin()

    base_query = ("SELECT tr.id, tr.test_id, tr.start_time, tr.end_time, tr.metrics, "
                  "tc.endpoint, tc.method, tc.user_id "
                  "FROM test_results tr "
                  "JOIN test_configs tc ON tr.test_id = tc.id")

    if not is_admin:
        base_query += f" WHERE user_id = {user_id}"

    cursor.execute(base_query)
    results = cursor.fetchall()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Test ID', 'Start Time', 'End Time', 'Metrics', 'Endpoint', 'Method', 'User ID'])

    for result in results:
        writer.writerow([
            result.id,
            result.test_id,
            result.start_time,
            result.end_time,
            result.metrics,
            result.endpoint,
            result.method,
            result.user_id
        ])
    output.seek(0)

    csv_string = output.getvalue()
    output_bytes = BytesIO(csv_string.encode('utf-8'))

    output_bytes.seek(0)

    return send_file(output_bytes, as_attachment=True, mimetype='text/csv', download_name='results_export.csv')