import sqlite3
from sqlite3 import Error

from bot_logger import get_logger

_logger = get_logger(__name__)


# ------------------------------------------------------------
class ParseError(Exception):
    pass


# Пример кортежа идущего в БД на вставку
# (123456, "test.dev.domain.ru", "Тестовый сертификат", '2023-06-10')
# ------------------------------------------------------------
class CertModel:
    # _INPUT_FIELDS = ("exp_date", "cn", "description")

    def __init__(self, db_row):
        """На вход ожидает кортеж формата:
        (id, user_id, common_namen, description, exp_date)
        """
        self.id = db_row[0]
        self.user_id = db_row[1]
        self.cn = db_row[2]
        self.description = db_row[3]
        self.exp_date = db_row[4]

    def __str__(self):
        return "{}; {}; {}".format(self.exp_date, self.cn, self.description)

    def list_to_string_list(model_list):
        return [str(cert) for cert in model_list]

    def from_string(cert_str):
        parts = cert_str.split(";")
        if len(parts) != 3:
            raise ParseError("Не удалось разобрать данные: " + cert_str)

        return CertModel((None, None, parts[1].strip(), parts[2].strip(), parts[0].strip()))


# ------------------------------------------------------------
class CertStore:
    _ALL_DB_FIELDS = ("id", "user_id", "cn", "description", "exp_date")
    _INSERT_DB_FIELDS = ("user_id", "cn", "description", "exp_date")
    _INSERT_DB_FIELDS_STR = ",".join(_INSERT_DB_FIELDS)

    _CREATE_CERT_TABLE = """create table if not exists cert(
    id integer primary key,
    user_id long,
    cn string,
    description string,
    exp_date date
    );"""

    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = self._create_connection(db_file)

        self._create_table(self._CREATE_CERT_TABLE)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def add_cert(self, cert):
        try:
            cur = self.conn.cursor()
            cur.execute(f"insert into cert( {CertStore._INSERT_DB_FIELDS_STR} ) values(?,?,?,?);",
                        (cert.user_id, cert.cn, cert.description, cert.exp_date))
            self.conn.commit()
            cert.id = cur.lastrowid
        except Error as e:
            _logger.exception("Ошибка записи в БД: " + str(e))
            raise
        return cert

    def delete_cert(self, user_id, cert_id):
        try:
            cur = self.conn.cursor()
            cur.execute("delete from cert where id = ? and user_id = ?;", (cert_id, user_id))
            self.conn.commit()
        except Error as e:
            _logger.exception("Ошибка удаления записи из БД: " + str(e))
            raise

    def get_cert(self, user_id, cert_id):
        try:
            cur = self.conn.cursor()
            cur.execute("select id, user_id, cn, description, exp_date from cert where id = ? and user_id = ?;",
                        (cert_id, user_id))
            rows = cur.fetchall()
        except Error as e:
            _logger.exception("Ошибка получения записи из БД: " + str(e))
            raise
        return CertStore.rows_to_cert_model(rows)

    def find_by_cn(self, user_id, common_name):
        try:
            cur = self.conn.cursor()
            cur.execute("select id, user_id, cn, description, exp_date from cert where user_id = ? and cn = ?;",
                        (user_id, common_name))
            rows = cur.fetchall()
        except Error as e:
            _logger.exception("Ошибка поиска записи в БД: " + str(e))
            raise e
        return CertStore.rows_to_cert_model(rows)

    def find_all_certs(self, user_id):
        try:
            cur = self.conn.cursor()
            cur.execute(
                "select id, user_id, cn, description, exp_date from cert where user_id = ? order by exp_date, cn desc;",
                (user_id, ))
            rows = cur.fetchall()
        except Error as e:
            print(e)
            raise e
        return CertStore.rows_to_cert_model(rows)

    def close(self):
        self.conn.close()

    def rows_to_cert_model(rows):
        return [CertModel(row) for row in rows]

    def _create_connection(self, db_file):
        """ Create database connection to SQLite database
        specified by db_file
        param db_file: string with path to db file
        return: connection object or None
        """
        try:
            self.conn = sqlite3.connect(db_file)
        except Error as e:
            print(e)
            raise e
        return self.conn

    def _create_table(self, create_table_sql):
        """ create a table from the create_table_sql statement
        :param conn: Connection object
        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
        try:
            c = self.conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)
