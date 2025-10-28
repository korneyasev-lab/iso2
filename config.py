"""
Конфигурация проекта ISO2
Настройки путей к папкам и константы
"""

import os
import json
import sys

# Базовая директория проекта (где лежит исполняемый файл)
if getattr(sys, 'frozen', False):
    # Если запущено из .app или .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Если запущено как Python скрипт
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Файл настроек (рядом с программой)
SETTINGS_FILE = os.path.join(BASE_DIR, "iso2_settings.json")

# Загружаем настройки
def load_settings():
    """Загрузить настройки из файла"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_settings(settings):
    """Сохранить настройки в файл"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

# Загружаем путь к рабочей папке
settings = load_settings()
WORK_DIR = settings.get('work_dir', None)

# Если путь не задан - будет None, GUI покажет диалог выбора
if WORK_DIR and os.path.exists(WORK_DIR):
    DOCS_DIR = WORK_DIR
else:
    DOCS_DIR = None

# Пути к папкам документов (будут установлены после выбора рабочей папки)
if DOCS_DIR:
    PROJECTS_DIR = os.path.join(DOCS_DIR, "ПРОЕКТЫ")
    ACTIVE_DIR = os.path.join(DOCS_DIR, "ДЕЙСТВУЮЩИЕ")
    ARCHIVE_DIR = os.path.join(DOCS_DIR, "АРХИВ")
    REGISTRIES_DIR = os.path.join(DOCS_DIR, "РЕЕСТРЫ")
else:
    PROJECTS_DIR = None
    ACTIVE_DIR = None
    ARCHIVE_DIR = None
    REGISTRIES_DIR = None

# Категории документов
CATEGORIES = [
    "НД СМК",
    "Шаблоны отчетов",
    "Формы записей",
    "ТИ"
]

# Пути к категориям (будут инициализированы после выбора рабочей папки)
ACTIVE_CATEGORIES = {}
ARCHIVE_CATEGORIES = {}
REGISTRIES_CATEGORIES = {}
REGISTRY_ACTUAL_FILES = {}

def init_category_paths():
    """Инициализация путей к категориям после установки DOCS_DIR"""
    global ACTIVE_CATEGORIES, ARCHIVE_CATEGORIES, REGISTRIES_CATEGORIES, REGISTRY_ACTUAL_FILES

    if not DOCS_DIR:
        return

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


def set_work_dir(work_dir):
    """
    Установить рабочую папку и пересоздать все пути

    Args:
        work_dir: Путь к рабочей папке (где будут храниться docs)

    Returns:
        bool: True если успешно
    """
    global DOCS_DIR, PROJECTS_DIR, ACTIVE_DIR, ARCHIVE_DIR, REGISTRIES_DIR

    # Сохраняем в настройки
    settings = load_settings()
    settings['work_dir'] = work_dir
    if not save_settings(settings):
        return False

    # Обновляем пути
    DOCS_DIR = work_dir
    PROJECTS_DIR = os.path.join(DOCS_DIR, "ПРОЕКТЫ")
    ACTIVE_DIR = os.path.join(DOCS_DIR, "ДЕЙСТВУЮЩИЕ")
    ARCHIVE_DIR = os.path.join(DOCS_DIR, "АРХИВ")
    REGISTRIES_DIR = os.path.join(DOCS_DIR, "РЕЕСТРЫ")

    # Инициализируем пути к категориям
    init_category_paths()

    # Создаём структуру папок
    create_folders()

    return True


def create_folders():
    """Создать структуру папок, если их нет"""
    if not DOCS_DIR:
        return

    # Основные папки
    base_folders = [DOCS_DIR, PROJECTS_DIR, ACTIVE_DIR, ARCHIVE_DIR, REGISTRIES_DIR]

    for folder in base_folders:
        if folder and not os.path.exists(folder):
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


# Если папка уже настроена - инициализируем пути
if DOCS_DIR:
    init_category_paths()