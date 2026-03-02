import sys
from pathlib import Path


# Добавляем корень проекта в sys.path, чтобы модуль app находился при запуске pytest
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

