"""Модуль для работы с сертификатами в БД sqlite3"""

import sqlite3
from sqlite3 import Error
from typing import Optional, Tuple, TypeVar, Type, List, Union, Text

from tcbot.logger import get_logger

_logger = get_logger(__name__)

_CertModelT = TypeVar("_CertModelT", bound="CertModel")
_CertStoreT = TypeVar("_CertStoreT", bound="CertStore")


# ------------------------------------------------------------
class ParseError(Exception):
    """Тип ошибки возникающей при разборе ввода от пользователя"""


# Пример кортежа идущего в БД на вставку
# (123456, "test.dev.domain.ru", "Тестовый сертификат", '2023-06-10')
# ------------------------------------------------------------
class CertModel:
    """Модель данных описывающая сертификат"""

    # _INPUT_FIELDS = ("exp_date", "cn", "description")

    # pylint: disable=too-many-arguments
    def __init__(self, rec_id: Optional[int], user_id: Optional[int], common_name: str,
                 description: str, exp_date: str) -> None:
        self.rec_id = rec_id
        self.user_id = user_id
        self.common_name = common_name
        self.description = description
        self.exp_date = exp_date

    def __str__(self) -> str:
        return f"{self.exp_date}; {self.common_name}; {self.description}"

    @classmethod
    def from_db_row(cls: Type[_CertModelT], db_row: Tuple[int, int, str, str,
                                                          str]) -> _CertModelT:
        """На вход ожидает кортеж формата:
        (rec_id, user_id, common_name, description, exp_date)
        """
        return cls(db_row[0],
                   db_row[1],
                   common_name=db_row[2],
                   description=db_row[3],
                   exp_date=db_row[4])

    @staticmethod
    def list_to_string_list(model_list: List[_CertModelT]) -> List[str]:
        """Конвертирует список объектов CertModel в список строк"""
        return [str(cert) for cert in model_list]

    @classmethod
    def from_string(cls: Type[_CertModelT], cert_str: str) -> _CertModelT:
        """Разбирает строку и создает новый экземпляр CertModel
        на основании результатов разбора.
        Ожидается стрка вида: 'common_name; description; exp_date',
        где exp_date - строка с датой в виде dd.mm.yyyy"""
        parts = cert_str.split(";")
        if len(parts) != 3:
            raise ParseError("Не удалось разобрать данные: " + cert_str)

        return cls(rec_id=None,
                   user_id=None,
                   common_name=parts[1].strip(),
                   description=parts[2].strip(),
                   exp_date=parts[0].strip())


# ------------------------------------------------------------
class CertStore:
    """Клсаа для работы с сертификатами в БД sqlite3"""
    _ALL_DB_FIELDS = ("id", "user_id", "cn", "description", "exp_date")
    _ALL_DB_FIELDS_STR = ",".join(_ALL_DB_FIELDS)
    _INSERT_DB_FIELDS = ("user_id", "cn", "description", "exp_date")
    _INSERT_DB_FIELDS_STR = ",".join(_INSERT_DB_FIELDS)

    _CREATE_CERT_TABLE = """create table if not exists cert(
    id integer primary key,
    user_id long,
    cn string,
    description string,
    exp_date date
    );"""

    def __init__(self, db_file: Union[bytes, Text]):
        self.db_file = db_file
        self.conn = self._create_connection(db_file)

        self._create_table(self._CREATE_CERT_TABLE)

    def __enter__(self: _CertStoreT) -> _CertStoreT:
        """Поддержка протокола with, вход в блок with"""
        return self

    def __exit__(self, exc_type: Type[Exception], exc_value: Exception,
                 traceback: str) -> None:
        """Поддержка протокола with, выход из блока with"""
        self.close()

    def add_cert(self, cert: CertModel) -> CertModel:
        """Сохраняет новый сертификат в БД"""
        try:
            cur = self.conn.cursor()
            cur.execute(
                f"insert into cert( {CertStore._INSERT_DB_FIELDS_STR} ) " +
                "values(?,?,?,?);",
                (cert.user_id, cert.common_name, cert.description, cert.exp_date))
            self.conn.commit()
            cert.rec_id = cur.lastrowid
        except Error as exc:
            _logger.exception("%s Ошибка записи в БД: %s", type(exc), exc)
            raise
        return cert

    def delete_cert(self, user_id: int, cert_id: int) -> None:
        """Удаляет существущий сертификат из БД"""
        try:
            cur = self.conn.cursor()
            cur.execute("delete from cert where id = ? and user_id = ?;",
                        (cert_id, user_id))
            self.conn.commit()
        except Error as exc:
            _logger.exception("%s Ошибка удаления записи из БД: %s", type(exc), exc)
            raise

    def get_cert(self, user_id: int, cert_id: int) -> List[CertModel]:
        """Ищет сертификат в БД по его id для заданного пользователя"""
        try:
            cur = self.conn.cursor()
            cur.execute(
                f"select {CertStore._ALL_DB_FIELDS_STR} from cert " +
                "where id = ? and user_id = ?;", (cert_id, user_id))
            rows = cur.fetchall()
        except Error as exc:
            _logger.exception("%s Ошибка получения записи из БД: %s", type(exc), exc)
            raise
        return CertStore.rows_to_cert_model(rows)

    def find_by_cn(self, user_id: int, common_name: str) -> List[CertModel]:
        """Ищет сертификат в БД по его common_name для заданного пользователя"""
        try:
            cur = self.conn.cursor()
            cur.execute(
                f"select {CertStore._ALL_DB_FIELDS_STR} from cert " +
                "where user_id = ? and cn = ?;", (user_id, common_name))
            rows = cur.fetchall()
        except Error as exc:
            _logger.exception("%s Ошибка поиска записи в БД: %s", type(exc), exc)
            raise
        return CertStore.rows_to_cert_model(rows)

    def find_all_certs(self, user_id: int) -> List[CertModel]:
        """Ищет все сертификаты в БД для заданного пользователя"""
        try:
            cur = self.conn.cursor()
            cur.execute(
                f"select {CertStore._ALL_DB_FIELDS_STR} from cert " +
                "where user_id = ? order by exp_date, cn desc;", (user_id, ))
            rows = cur.fetchall()
        except Error as exc:
            _logger.exception("%s Ошибка получения записи из БД: %s", type(exc), exc)
            raise
        return CertStore.rows_to_cert_model(rows)

    def close(self) -> None:
        """Закрывает соединение с БД"""
        self.conn.close()

    @staticmethod
    def rows_to_cert_model(
            rows: List[Tuple[int, int, str, str, str]]) -> List[CertModel]:
        """Принимает строки из БД в виде кортежей и возвращает
        в виде списка объектов CertModel"""
        return [CertModel.from_db_row(row) for row in rows]

    def _create_connection(self, db_file: Union[bytes, Text]) -> sqlite3.Connection:
        """ Create database connection to SQLite database
        specified by db_file
        param db_file: string with path to db file
        return: connection object or None
        """
        try:
            self.conn = sqlite3.connect(db_file)
        except Error as exc:
            _logger.exception("%s Ошибка подключения к БД: %s", type(exc), exc)
            raise
        return self.conn

    def _create_table(self, create_table_sql: str) -> None:
        """ create a table from the create_table_sql statement
        :param conn: Connection object
        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
        try:
            cur = self.conn.cursor()
            cur.execute(create_table_sql)
        except Error as exc:
            _logger.exception("%s Ошибка создания таблицы БД: %s", type(exc), exc)
            raise
