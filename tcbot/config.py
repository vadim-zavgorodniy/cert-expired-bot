# ------------------------------------------------------------
# Конфигурация бота
# ------------------------------------------------------------

import os
import utils.path

# PROJECT_ROOT_DIR1 = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT_DIR = Path(__file__).parent.parent
PROJECT_ROOT_DIR = utils.path.get_project_root()

DB_FILE_NAME = os.path.join(PROJECT_ROOT_DIR, "bot_sqlite.db")

_TOKEN_FILE_NAME = os.path.join(PROJECT_ROOT_DIR, "token.txt")
BOT_TOKEN = None

try:
    with open(_TOKEN_FILE_NAME, "r") as f:
        BOT_TOKEN = f.readline().strip()
except Exception:
    print("Ошибка чтениия файла с токеном доступа к telegram боту: " + _TOKEN_FILE_NAME)
    raise
