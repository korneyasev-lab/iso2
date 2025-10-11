"""
Конфигурация проекта ISO2
Настройки путей к папкам и константы
"""

import os

# Базовая директория проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Пути к папкам документов
DOCS_DIR = os.path.join(BASE_DIR, "docs")
PROJECTS_DIR = os.path.join(DOCS_DIR, "ПРОЕКТЫ")
ACTIVE_DIR = os.path.join(DOCS_DIR, "ДЕЙСТВУЮЩИЕ")
ARCHIVE_DIR = os.path.join(DOCS_DIR, "АРХИВ")
REGISTRIES_DIR = os.path.join(DOCS_DIR, "РЕЕСТРЫ")

# Имя актуального реестра
REGISTRY_ACTUAL = os.path.join(REGISTRIES_DIR, "РЕЕСТР_АКТУАЛЬНЫЙ.txt")

# Типы документов (для фильтров)
DOCUMENT_TYPES = ["ПП", "РК", "ДИ", "ВНД", "ТР", "ТИ", "ТУ", "ГОСТ"]

# Диапазон годов
YEAR_MIN = 2000
YEAR_MAX = 2050

# Допустимые расширения файлов
ALLOWED_EXTENSIONS = [".docx", ".doc", ".pdf"]

# Количество реестров для хранения
REGISTRIES_KEEP_COUNT = 100

# Создание папок при первом запуске
def create_folders():
    """Создать структуру папок, если их нет"""
    for folder in [DOCS_DIR, PROJECTS_DIR, ACTIVE_DIR, ARCHIVE_DIR, REGISTRIES_DIR]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Создана папка: {folder}")

# Автоматическое создание папок при импорте
create_folders()