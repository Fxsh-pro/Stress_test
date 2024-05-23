import os

SECRET_KEY = b'afd41e94b269e053cc3f6d065a717cffde51ee5208928463ce897faed531006b'
DB_DATA = os.environ.get('DB_DATA')

MYSQL_USER = DB_DATA
MYSQL_PASSWORD = DB_DATA
MYSQL_HOST = 'rc1b-2xmunoaqhipsaggs.mdb.yandexcloud.net'
MYSQL_DATABASE = DB_DATA

ADMIN_ROLE_ID = 1