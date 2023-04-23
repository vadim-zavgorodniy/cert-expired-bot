"""Модуль с для подготовки конфигурации логирования"""

import logging
import logging.config
import os

from tcbot import config

_LOGGER_CONFIG_FILE_NAME = os.path.join(config.PROJECT_ROOT_DIR, "logger.conf")

logging.config.fileConfig(fname=_LOGGER_CONFIG_FILE_NAME,
                          disable_existing_loggers=False)


def get_logger(logger_name: str) -> logging.Logger:
    """Создает новый объект класса logging.Logger с заданным именем"""
    return logging.getLogger(logger_name)
