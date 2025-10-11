"""
Бизнес-логика ISO2
Парсинг имён файлов, сравнение документов, работа с реестрами
"""

import os
import re
import shutil
from datetime import datetime
from config import (
    PROJECTS_DIR, ACTIVE_DIR, ARCHIVE_DIR, REGISTRIES_DIR,
    REGISTRY_ACTUAL, ALLOWED_EXTENSIONS, YEAR_MIN, YEAR_MAX,
    REGISTRIES_KEEP_COUNT
)


class Document:
    """Класс для представления документа"""

    def __init__(self, filename, folder_path):
        self.filename = filename
        self.folder_path = folder_path
        self.full_path = os.path.join(folder_path, filename)

        # Парсим имя файла
        parsed = parse_filename(filename)
        self.typ = parsed.get("typ", "")
        self.kod = parsed.get("kod", "")
        self.version = parsed.get("version", "")
        self.year = parsed.get("year", "")
        self.title = parsed.get("title", "")
        self.is_valid = parsed.get("is_valid", False)

    def __repr__(self):
        return f"Document({self.filename})"


def parse_filename(filename):
    """
    Парсинг имени файла документа

    Формат: ТИП.КОД-ВЕРСИЯ-ГОД НАЗВАНИЕ.docx
    Пример: ПП.К2-8.3-01-2022 Управление документацией.docx

    Returns:
        dict: {typ, kod, version, year, title, is_valid}
    """
    # Убираем расширение
    name_without_ext = os.path.splitext(filename)[0]

    # Ищем первый пробел (отделяет метаданные от названия)
    match = re.match(r'^([^\s]+)\s+(.+)$', name_without_ext)

    if not match:
        return {
            "typ": "",
            "kod": "",
            "version": "",
            "year": "",
            "title": filename,
            "is_valid": False
        }

    metadata = match.group(1)  # ПП.К2-8.3-01-2022
    title = match.group(2)     # Управление документацией

    # Разбираем метаданные
    # Формат: ТИП.КОД-ВЕРСИЯ-ГОД
    # Сначала ищем год (последнее число 2000-2050)
    parts = metadata.split('-')

    if len(parts) < 3:
        return {
            "typ": "",
            "kod": "",
            "version": "",
            "year": "",
            "title": title,
            "is_valid": False
        }

    # Год - последняя часть
    year = parts[-1]

    # Проверяем год
    try:
        year_int = int(year)
        if not (YEAR_MIN <= year_int <= YEAR_MAX):
            return {
                "typ": "",
                "kod": "",
                "version": "",
                "year": "",
                "title": title,
                "is_valid": False
            }
    except ValueError:
        return {
            "typ": "",
            "kod": "",
            "version": "",
            "year": "",
            "title": title,
            "is_valid": False
        }

    # Версия - предпоследняя часть
    version = parts[-2]

    # ТИП.КОД - всё что до версии
    type_kod = '-'.join(parts[:-2])

    # Разделяем ТИП и КОД по точке
    if '.' not in type_kod:
        return {
            "typ": "",
            "kod": type_kod,
            "version": version,
            "year": year,
            "title": title,
            "is_valid": False
        }

    type_parts = type_kod.split('.', 1)
    typ = type_parts[0]
    kod = type_parts[1] if len(type_parts) > 1 else ""

    return {
        "typ": typ,
        "kod": kod,
        "version": version,
        "year": year,
        "title": title,
        "is_valid": True
    }


def build_filename(typ, kod, version, year, title):
    """
    Сборка имени файла из компонентов

    Args:
        typ: Тип документа (ПП, РК, ВНД и т.д.)
        kod: Код документа (К2-8.3, О1-8.4 и т.д.)
        version: Версия (01, 02 и т.д.)
        year: Год (2022, 2025 и т.д.)
        title: Название документа

    Returns:
        str: Имя файла (без расширения)
    """
    return f"{typ}.{kod}-{version}-{year} {title}"


def scan_folder(folder_path):
    """
    Сканирование папки и парсинг всех документов

    Args:
        folder_path: Путь к папке

    Returns:
        list[Document]: Список документов
    """
    documents = []

    if not os.path.exists(folder_path):
        return documents

    for filename in os.listdir(folder_path):
        # Проверяем расширение
        ext = os.path.splitext(filename)[1].lower()
        if ext in ALLOWED_EXTENSIONS:
            doc = Document(filename, folder_path)
            documents.append(doc)

    return documents


def find_similar_documents(doc, documents_list):
    """
    Поиск похожих документов (по коду ИЛИ названию)

    Args:
        doc: Document для сравнения
        documents_list: Список документов для поиска

    Returns:
        list[Document]: Список похожих документов
    """
    similar = []

    for other_doc in documents_list:
        # Пропускаем сам документ
        if doc.filename == other_doc.filename:
            continue

        # Проверяем совпадение по коду или названию
        kod_match = (doc.kod == other_doc.kod and doc.kod != "")
        title_match = (doc.title.lower() == other_doc.title.lower() and doc.title != "")

        if kod_match or title_match:
            similar.append(other_doc)

    return similar


def compare_documents(doc1, doc2):
    """
    Сравнение двух документов - выявление совпадений и различий

    Args:
        doc1: Первый документ
        doc2: Второй документ

    Returns:
        dict: {matches: [], differences: []}
    """
    matches = []
    differences = []

    # Сравниваем поля
    fields = [
        ("ТИП", doc1.typ, doc2.typ),
        ("КОД", doc1.kod, doc2.kod),
        ("ВЕРСИЯ", doc1.version, doc2.version),
        ("ГОД", doc1.year, doc2.year),
        ("НАЗВАНИЕ", doc1.title, doc2.title)
    ]

    for field_name, val1, val2 in fields:
        if val1 == val2 and val1 != "":
            matches.append(f"{field_name}({val1})")
        elif val1 != val2 and val1 != "" and val2 != "":
            differences.append(f"{field_name}({val1}≠{val2})")

    return {
        "matches": matches,
        "differences": differences
    }


def publish_document(source_doc, typ, kod, version, year, title, archive_list):
    """
    Публикация документа:
    1. Собрать новое имя
    2. Скопировать из ПРОЕКТОВ в ДЕЙСТВУЮЩИЕ
    3. Удалить из ПРОЕКТОВ
    4. Переместить выбранные документы в АРХИВ
    5. Создать новый реестр

    Args:
        source_doc: Document из папки ПРОЕКТЫ
        typ, kod, version, year, title: Новые данные документа
        archive_list: Список документов для перемещения в архив

    Returns:
        bool: True если успешно
    """
    try:
        # 1. Собираем новое имя
        new_filename = build_filename(typ, kod, version, year, title)
        ext = os.path.splitext(source_doc.filename)[1]
        new_filename_full = new_filename + ext

        # 2. Копируем в ДЕЙСТВУЮЩИЕ
        dest_path = os.path.join(ACTIVE_DIR, new_filename_full)
        shutil.copy2(source_doc.full_path, dest_path)

        # 3. Удаляем из ПРОЕКТОВ
        os.remove(source_doc.full_path)

        # 4. Перемещаем выбранные в АРХИВ
        for doc_to_archive in archive_list:
            archive_path = os.path.join(ARCHIVE_DIR, doc_to_archive.filename)
            shutil.move(doc_to_archive.full_path, archive_path)

        # 5. Создаём новый реестр
        create_registry()

        return True

    except Exception as e:
        print(f"Ошибка при публикации: {e}")
        return False


def get_last_registry_number():
    """
    Получить номер последнего реестра

    Returns:
        int: Номер последнего реестра (0 если реестров нет)
    """
    if not os.path.exists(REGISTRIES_DIR):
        return 0

    numbers = []
    pattern = re.compile(r'^РЕЕСТР_(\d{3})_\d{4}-\d{2}-\d{2}\.txt$')

    for filename in os.listdir(REGISTRIES_DIR):
        match = pattern.match(filename)
        if match:
            numbers.append(int(match.group(1)))

    return max(numbers) if numbers else 0


def create_registry():
    """
    Создать новый реестр действующих документов

    Формат имени: РЕЕСТР_XXX_ГГГГ-ММ-ДД.txt
    """
    # 1. Номер нового реестра
    last_number = get_last_registry_number()
    new_number = last_number + 1

    # 2. Текущая дата
    today = datetime.now().strftime("%Y-%m-%d")
    time_now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    # 3. Имя файла
    filename = f"РЕЕСТР_{new_number:03d}_{today}.txt"
    filepath = os.path.join(REGISTRIES_DIR, filename)

    # 4. Сканируем действующие документы
    active_docs = scan_folder(ACTIVE_DIR)

    # Сортируем по имени файла
    active_docs.sort(key=lambda d: d.filename)

    # 5. Формируем содержимое реестра
    content = []
    content.append("═" * 80)
    content.append("РЕЕСТР ДЕЙСТВУЮЩИХ ДОКУМЕНТОВ СМК")
    content.append(f"Версия: {new_number}")
    content.append(f"Дата создания: {time_now}")
    content.append("═" * 80)
    content.append("")

    # Список документов (собранные имена без расширения)
    for i, doc in enumerate(active_docs, 1):
        if doc.is_valid:
            # Собираем имя: ТИП.КОД-ВЕРСИЯ-ГОД НАЗВАНИЕ
            doc_name = build_filename(doc.typ, doc.kod, doc.version, doc.year, doc.title)
            content.append(f"{i}. {doc_name}")
        else:
            # Если не распарсилось - показываем как есть
            content.append(f"{i}. {doc.filename}")

    content.append("")
    content.append("═" * 80)
    content.append(f"ИТОГО: {len(active_docs)} действующих документов")
    content.append("═" * 80)

    # 6. Записываем в файл
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

    # 7. Копируем в АКТУАЛЬНЫЙ
    shutil.copy2(filepath, REGISTRY_ACTUAL)

    # 8. Очищаем старые реестры
    cleanup_old_registries()

    print(f"Создан реестр: {filename}")


def cleanup_old_registries():
    """
    Удалить старые реестры, оставить только последние REGISTRIES_KEEP_COUNT
    """
    if not os.path.exists(REGISTRIES_DIR):
        return

    # Получаем все файлы реестров
    pattern = re.compile(r'^РЕЕСТР_(\d{3})_\d{4}-\d{2}-\d{2}\.txt$')
    registries = []

    for filename in os.listdir(REGISTRIES_DIR):
        match = pattern.match(filename)
        if match:
            filepath = os.path.join(REGISTRIES_DIR, filename)
            registries.append((int(match.group(1)), filepath))

    # Сортируем по номеру
    registries.sort(key=lambda x: x[0])

    # Если больше REGISTRIES_KEEP_COUNT - удаляем старые
    if len(registries) > REGISTRIES_KEEP_COUNT:
        to_delete = registries[:-REGISTRIES_KEEP_COUNT]
        for number, filepath in to_delete:
            os.remove(filepath)
            print(f"Удалён старый реестр: {os.path.basename(filepath)}")