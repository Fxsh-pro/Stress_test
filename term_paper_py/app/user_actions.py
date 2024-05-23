from io import BytesIO
from math import ceil

from flask import Blueprint, render_template, request, send_file, Response
from flask_login import current_user, login_required

from app import db_operation
from auto import check_for_privelege

# create table user_actions (
#     id int primary key auto_increment,
#     user_id int,
#     path varchar(100) not null,
#     created_at timestamp default current_timestamp,
#     foreign key (user_id) references users(id)
# ) engine innodb

bp = Blueprint('user_actions', __name__, url_prefix='/user_actions')
MAX_PER_PAGE = 10


@bp.route('/')
@db_operation
def index(cursor):
    page = request.args.get('page', 1, type=int)
    user_id = current_user.get_id()
    is_admin = current_user.is_authenticated and current_user.is_admin()
    is_authenticated = current_user.is_authenticated

    base_query = ("SELECT last_name, first_name, middle_name, "
                  "path, user_actions.created_at AS created_at "
                  "FROM user_actions LEFT JOIN users ON user_actions.user_id = users.id ")
    params = ()
    count_query_condition = ""

    if is_authenticated:
        if not is_admin:
            base_query += "WHERE user_actions.user_id = %s "
            count_query_condition = "WHERE user_id = %s"
            params = (user_id,)
    else:
        base_query += "WHERE user_actions.user_id is null "
        count_query_condition = "WHERE user_id is null"

    query_limit = base_query + "LIMIT %s OFFSET %s"
    cursor.execute(query_limit, params + (MAX_PER_PAGE, (page - 1) * MAX_PER_PAGE))
    actions = cursor.fetchall()

    count_query = "SELECT COUNT(*) as count FROM user_actions " + count_query_condition
    cursor.execute(count_query, params if params else ())
    record_count = cursor.fetchone().count

    page_count = ceil(record_count / MAX_PER_PAGE)
    pages = range(max(1, page - 3), min(page_count, page + 3) + 1)

    return render_template("user_actions/index.html", user_actions=actions,
                           page=page, pages=pages, page_count=page_count)


def fetch_user_stats(cursor):
    query = """
        SELECT user_id, last_name, first_name, middle_name, 
        COUNT(*) AS entries_counter 
        FROM user_actions LEFT JOIN users ON user_actions.user_id = users.id 
        GROUP BY user_id
    """
    cursor.execute(query)
    return cursor.fetchall()


def fetch_page_stats(cursor):
    query = """
        SELECT path, COUNT(*) AS visits_count 
        FROM user_actions
        GROUP BY path 
        ORDER BY visits_count DESC
    """
    cursor.execute(query)
    return cursor.fetchall()


@bp.route('users_stats')
@db_operation
@login_required
@check_for_privelege('read_statistics')
def users_stats(cursor):
    users_stats = fetch_user_stats(cursor)
    return render_template("user_actions/users_stats.html", users_stats=users_stats)


@bp.route('user_export.csv')
@db_operation
@login_required
@check_for_privelege('read_statistics')
def user_export(cursor):
    users_stats = fetch_user_stats(cursor)

    result = ''
    fields = ['last_name', 'first_name', 'middle_name', 'entries_counter']
    none_values = ['не', 'авторизованный', 'пользователь']
    result += ','.join(fields) + '\n'
    for record in users_stats:
        if record.user_id is None:
            result += ','.join(none_values) + ',' + str(record.entries_counter) + '\n'
            continue
        result += ','.join([str(getattr(record, field)) for field in fields]) + '\n'

    return send_file(BytesIO(result.encode()), as_attachment=True, mimetype='text/csv', download_name='user_export.csv')


@bp.route('/pages_stats')
@db_operation
@login_required
@check_for_privelege('read_statistics')
def pages_stats(cursor):
    pages_stats = fetch_page_stats(cursor)
    return render_template("user_actions/pages_stats.html", pages_stats=pages_stats)


@bp.route('/pages_export.csv')
@db_operation
@login_required
@check_for_privelege('read_statistics')
def pages_export(cursor):
    pages_stats = fetch_page_stats(cursor)

    result = '№,Page,Visits Count\n'
    for index, record in enumerate(pages_stats, start=1):
        result += f'{index},{record.path},{record.visits_count}\n'

    return send_file(BytesIO(result.encode()), as_attachment=True, mimetype='text/csv',
                     download_name='pages_export.csv')
