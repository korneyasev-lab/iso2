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

# Категории документов
CATEGORIES = [
    "НД СМК",
    "Шаблоны отчетов",
    "Формы записей",
    "ТИ"
]

# Пути к категориям в ДЕЙСТВУЮЩИЕ
ACTIVE_CATEGORIES = {
    "НД СМК": os.path.join(ACTIVE_DIR, "НД СМК"),
    "Шаблоны отчетов": os.path.join(ACTIVE_DIR, "Шаблоны отчетов"),
    "Формы записей": os.path.join(ACTIVE_DIR, "Формы записей"),
    "ТИ": os.path.join(ACTIVE_DIR, "ТИ")
}

# Пути к категориям в АРХИВ
ARCHIVE_CATEGORIES = {
    "НД СМК": os.path.join(ARCHIVE_DIR, "НД СМК"),
    "Шаблоны отчетов": os.path.join(ARCHIVE_DIR, "Шаблоны отчетов"),
    "Формы записей": os.path.join(ARCHIVE_DIR, "Формы записей"),
    "ТИ": os.path.join(ARCHIVE_DIR, "ТИ")
}

# Пути к категориям в РЕЕСТРЫ
REGISTRIES_CATEGORIES = {
    "НД СМК": os.path.join(REGISTRIES_DIR, "НД СМК"),
    "Шаблоны отчетов": os.path.join(REGISTRIES_DIR, "Шаблоны отчетов"),
    "Формы записей": os.path.join(REGISTRIES_DIR, "Формы записей"),
    "ТИ": os.path.join(REGISTRIES_DIR, "ТИ")
}

# Имена актуальных реестров для каждой категории
REGISTRY_ACTUAL_FILES = {
    "НД СМК": os.path.join(REGISTRIES_CATEGORIES["НД СМК"], "РЕЕСТР_НД_СМК_АКТУАЛЬНЫЙ.txt"),
    "Шаблоны отчетов": os.path.join(REGISTRIES_CATEGORIES["Шаблоны отчетов"], "РЕЕСТР_Шаблоны_отчетов_АКТУАЛЬНЫЙ.txt"),
    "Формы записей": os.path.join(REGISTRIES_CATEGORIES["Формы записей"], "РЕЕСТР_Формы_записей_АКТУАЛЬНЫЙ.txt"),
    "ТИ": os.path.join(REGISTRIES_CATEGORIES["ТИ"], "РЕЕСТР_ТИ_АКТУАЛЬНЫЙ.txt")
}

# Типы документов (для фильтров)
DOCUMENT_TYPES = ["ПП", "РК", "ДИ", "ВНД", "ТР", "ТИ", "ТУ", "ГОСТ"]

# Диапазон годов
YEAR_MIN = 2000
YEAR_MAX = 2050

# Допустимые расширения файлов
ALLOWED_EXTENSIONS = [".docx", ".doc", ".pdf"]

# Количество реестров для хранения
REGISTRIES_KEEP_COUNT = 100


def create_folders():
    """Создать структуру папок, если их нет"""
    # Основные папки
    base_folders = [DOCS_DIR, PROJECTS_DIR, ACTIVE_DIR, ARCHIVE_DIR, REGISTRIES_DIR]

    for folder in base_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Создана папка: {folder}")

    # Категории в ДЕЙСТВУЮЩИЕ
    for category, path in ACTIVE_CATEGORIES.items():
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Создана папка: {path}")

    # Категории в АРХИВ
    for category, path in ARCHIVE_CATEGORIES.items():
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Создана папка: {path}")

    # Категории в РЕЕСТРЫ
    for category, path in REGISTRIES_CATEGORIES.items():
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Создана папка: {path}")


# Автоматическое создание папок при импорте
create_folders()