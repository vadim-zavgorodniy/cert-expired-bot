"""Модуль для работы с сертификатами в БД sqlite3"""

from sqlite3 import Error

from datetime import datetime, date

from typing import Tuple, TypeVar, Type, Optional, Sequence, Any

from sqlalchemy import create_engine, Engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
# from sqlalchemy.ext.hybrid import hybrid_property

from tcbot.logger import get_logger

_logger = get_logger(__name__)

_CertModelT = TypeVar("_CertModelT", bound="CertModel")
_CertStoreT = TypeVar("_CertStoreT", bound="CertStore")


# ------------------------------------------------------------
# pylint: disable=too-few-public-methods
class Base(DeclarativeBase):
    """Базовый класс для описания моделей"""


# ------------------------------------------------------------
class ParseError(Exception):
    """Тип ошибки возникающей при разборе ввода от пользователя"""


# Пример кортежа идущего в БД на вставку
# (123456, "test.dev.domain.ru", "Тестовый сертификат", '2023-06-10')
# ------------------------------------------------------------
class CertModel(Base):
    """Модель данных описывающая сертификат"""

    __tablename__ = "cert"

    rec_id: Mapped[int] = mapped_column("id", primary_key=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
    common_name: Mapped[str] = mapped_column("cn",
                                             nullable=False,
                                             index=True,
                                             unique=True)
    description: Mapped[str] = mapped_column(nullable=False)
    _exp_date: Mapped[date] = mapped_column("exp_date", nullable=False)

    # pylint: disable=too-many-arguments
    def __init__(self, exp_date: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.exp_date = exp_date

    @property
    def exp_date(self) -> str:
        """Получение даты в виде строки"""
        return self._exp_date.strftime("%d.%m.%Y")

    @exp_date.setter
    def exp_date(self, exp_date: str) -> None:
        self._exp_date = datetime.strptime(exp_date, "%d.%m.%Y").date()

    def __repr__(self) -> str:
        return f"{self.exp_date}; {self.common_name}; {self.description}"

    @classmethod
    def from_db_row(cls: Type[_CertModelT], db_row: Tuple[int, int, str, str,
                                                          str]) -> _CertModelT:
        """На вход ожидает кортеж формата:
        (rec_id, user_id, common_name, description, exp_date)
        """
        return cls(rec_id=db_row[0],
                   user_id=db_row[1],
                   common_name=db_row[2],
                   description=db_row[3],
                   exp_date=db_row[4])

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

    @staticmethod
    def seq_to_string_list(model_list: Sequence[_CertModelT]) -> list[str]:
        """Конвертирует последовательность объектов CertModel в список строк"""
        return [str(cert) for cert in model_list]


# ------------------------------------------------------------
class CertStore:
    """Клсаc для работы с сертификатами в БД sqlite3 через sqlalchemy"""

    def __init__(self, db_file: str):
        self.db_file: str = db_file

        self.engine: Engine = create_engine(f"sqlite:///{self.db_file}")
        self._create_tables()
        self._session: Session = Session(self.engine)

    def __enter__(self: _CertStoreT) -> _CertStoreT:
        """Поддержка протокола with, вход в блок with"""
        return self

    def __exit__(self, exc_type: Type[Exception], exc_value: Exception,
                 traceback: str) -> None:
        """Поддержка протокола with, выход из блока with"""
        self._session.close()

    def close(self) -> None:
        """Закрывает соединение с БД"""
        self._session.close()

    def add_cert(self, cert: CertModel) -> CertModel:
        """Сохраняет новый сертификат в БД"""
        try:
            self._session.add(cert)
            self._session.commit()
        except Error as exc:
            _logger.exception("%s Ошибка записи в БД: %s", type(exc), exc)
            raise
        return cert

    def delete_cert(self, cert: CertModel) -> None:
        """Удаляет существущий сертификат из БД"""
        try:
            self._session.delete(cert)
            self._session.commit()
        except Error as exc:
            _logger.exception("%s Ошибка удаления записи из БД: %s", type(exc), exc)
            raise

    def get_cert(self, user_id: int, cert_id: int) -> Optional[CertModel]:
        """Ищет сертификат в БД по его id для заданного пользователя"""
        try:
            stmt = select(CertModel).where(CertModel.rec_id == cert_id).where(
                CertModel.user_id == user_id)
            return self._session.scalars(stmt).first()
        except Error as exc:
            _logger.exception("%s Ошибка получения записи из БД: %s", type(exc), exc)
            raise

    def find_by_cn(self, user_id: int, common_name: str) -> Optional[CertModel]:
        """Ищет сертификат в БД по его common_name для заданного пользователя"""
        try:
            stmt = select(CertModel).where(CertModel.user_id == user_id).where(
                CertModel.common_name == common_name)
            return self._session.scalars(stmt).first()
        except Error as exc:
            _logger.exception("%s Ошибка поиска записи в БД: %s", type(exc), exc)
            raise

    def find_all_certs(self, user_id: int) -> Sequence[CertModel]:
        """Ищет все сертификаты в БД для заданного пользователя"""
        try:
            stmt = select(CertModel).where(CertModel.user_id == user_id)
            return self._session.scalars(stmt).all()
        except Error as exc:
            _logger.exception("%s Ошибка получения записи из БД: %s", type(exc), exc)
            raise

    def _create_engine(self, db_file: str) -> Engine:
        """Создает подключение к БД"""
        try:
            return create_engine(f"sqlite:///{db_file}")
        except Error as exc:
            _logger.exception("%s Ошибка подключения к БД: %s", type(exc), exc)
            raise

    def _create_tables(self) -> None:
        """Создает все необходимые таблицы"""
        try:
            Base.metadata.create_all(self.engine)
        except Error as exc:
            _logger.exception("%s Ошибка создания структуры БД: %s", type(exc), exc)
            raise
