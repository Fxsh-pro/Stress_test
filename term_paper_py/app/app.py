import datetime
from functools import wraps

from flask import Flask, render_template, session, request
from flask_login import current_user, login_required

from mysqldb import DBConnector

app = Flask(__name__)
application = app
app.config.from_pyfile('config.py')

db_connector = DBConnector(app)


def db_operation(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time, end_time = None, None
        connection = db_connector.connect()
        try:
            start_time = datetime.datetime.now()
            with connection.cursor(named_tuple=True, buffered=True) as cursor:
                result = func(cursor, *args, **kwargs)
                connection.commit()
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            end_time = datetime.datetime.now()
            print(f"Duration {func}: {end_time - start_time}")
            # connection.close()
        return result

    return wrapper


from auto import bp as auto_bp, init_login_manager

app.register_blueprint(auto_bp)
init_login_manager(app)

from users import bp as users_bp

app.register_blueprint(users_bp)

from user_actions import bp as user_actions_bp

app.register_blueprint(user_actions_bp)

from tests import bp as tests_bp

app.register_blueprint(tests_bp)


@app.before_request
@db_operation
def record_action(cursor):
    if request.endpoint == 'static':
        return
    user_id = current_user.id if current_user.is_authenticated else None
    path = request.path
    query = "INSERT INTO user_actions (user_id, path) VALUES (%s, %s)"
    cursor.execute(query, (user_id, path))


@app.route('/')
def index():
    return render_template('index.html')



