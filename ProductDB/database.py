"""
ProductDB - Database module
Функции для работы с базой данных SQLite
"""

import sqlite3
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple


class Database:
    """Класс для работы с базой данных ProductDB"""

    def __init__(self, db_path: str = "data/productdb.sqlite"):
        """
        Инициализация подключения к БД

        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.connection = None
        self.cursor = None

    def connect(self):
        """Установить соединение с БД"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Возвращать строки как словари
        self.cursor = self.connection.cursor()
        # Включить поддержку внешних ключей
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.connection.commit()

    def close(self):
        """Закрыть соединение с БД"""
        if self.connection:
            self.connection.close()

    def __enter__(self):
        """Контекстный менеджер: вход"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер: выход"""
        self.close()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Выполнить SQL запрос

        Args:
            query: SQL запрос
            params: Параметры запроса

        Returns:
            Курсор с результатами
        """
        return self.cursor.execute(query, params)

    def commit(self):
        """Зафиксировать изменения"""
        self.connection.commit()

    def rollback(self):
        """Откатить изменения"""
        self.connection.rollback()

    # ============================================
    # CLIENTS (Заказчики)
    # ============================================

    def add_client(self, name: str, contact_info: str = None, notes: str = None) -> int:
        """Добавить нового заказчика"""
        self.execute(
            "INSERT INTO clients (name, contact_info, notes) VALUES (?, ?, ?)",
            (name, contact_info, notes)
        )
        self.commit()
        return self.cursor.lastrowid

    def get_client(self, client_id: int) -> Optional[Dict]:
        """Получить заказчика по ID"""
        result = self.execute(
            "SELECT * FROM clients WHERE id = ?", (client_id,)
        ).fetchone()
        return dict(result) if result else None

    def get_all_clients(self) -> List[Dict]:
        """Получить всех заказчиков"""
        results = self.execute("SELECT * FROM clients ORDER BY name").fetchall()
        return [dict(row) for row in results]

    def update_client(self, client_id: int, name: str = None,
                     contact_info: str = None, notes: str = None) -> bool:
        """Обновить данные заказчика"""
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if contact_info is not None:
            updates.append("contact_info = ?")
            params.append(contact_info)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)

        if not updates:
            return False

        params.append(client_id)
        query = f"UPDATE clients SET {', '.join(updates)} WHERE id = ?"
        self.execute(query, tuple(params))
        self.commit()
        return True

    def delete_client(self, client_id: int) -> bool:
        """Удалить заказчика"""
        self.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        self.commit()
        return self.cursor.rowcount > 0

    # ============================================
    # PRODUCTS (Изделия)
    # ============================================

    def add_product(self, client_id: int, drawing_number: str, variant: str,
                   description: str = None, notes: str = None) -> int:
        """Добавить новое изделие"""
        self.execute(
            """INSERT INTO products (client_id, drawing_number, variant, description, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (client_id, drawing_number, variant, description, notes)
        )
        self.commit()
        return self.cursor.lastrowid

    def get_product(self, product_id: int) -> Optional[Dict]:
        """Получить изделие по ID"""
        result = self.execute(
            """SELECT p.*, c.name as client_name
               FROM products p
               JOIN clients c ON p.client_id = c.id
               WHERE p.id = ?""",
            (product_id,)
        ).fetchone()
        return dict(result) if result else None

    def get_products_by_client(self, client_id: int) -> List[Dict]:
        """Получить все изделия заказчика"""
        results = self.execute(
            """SELECT p.*, c.name as client_name
               FROM products p
               JOIN clients c ON p.client_id = c.id
               WHERE p.client_id = ?
               ORDER BY p.drawing_number, p.variant""",
            (client_id,)
        ).fetchall()
        return [dict(row) for row in results]

    def get_all_products(self) -> List[Dict]:
        """Получить все изделия"""
        results = self.execute(
            """SELECT p.*, c.name as client_name
               FROM products p
               JOIN clients c ON p.client_id = c.id
               ORDER BY c.name, p.drawing_number, p.variant"""
        ).fetchall()
        return [dict(row) for row in results]

    def delete_product(self, product_id: int) -> bool:
        """Удалить изделие"""
        self.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.commit()
        return self.cursor.rowcount > 0

    # ============================================
    # COMPONENTS (Комплектующие)
    # ============================================

    def add_component(self, type_id: int, name: str, unit: str,
                     concrete_brand: str = None, notes: str = None) -> int:
        """Добавить комплектующее"""
        self.execute(
            """INSERT INTO components (type_id, name, unit, concrete_brand, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (type_id, name, unit, concrete_brand, notes)
        )
        self.commit()
        return self.cursor.lastrowid

    def get_component(self, component_id: int) -> Optional[Dict]:
        """Получить комплектующее по ID"""
        result = self.execute(
            """SELECT c.*, ct.name as type_name
               FROM components c
               JOIN component_types ct ON c.type_id = ct.id
               WHERE c.id = ?""",
            (component_id,)
        ).fetchone()
        return dict(result) if result else None

    def get_all_components(self) -> List[Dict]:
        """Получить все комплектующие"""
        results = self.execute(
            """SELECT c.*, ct.name as type_name
               FROM components c
               JOIN component_types ct ON c.type_id = ct.id
               ORDER BY ct.name, c.name"""
        ).fetchall()
        return [dict(row) for row in results]

    # ============================================
    # COMPOSITIONS (Комплектация)
    # ============================================

    def add_composition(self, product_id: int, component_id: int, quantity: float,
                       notes: str = None) -> int:
        """Добавить комплектующее в состав изделия"""
        self.execute(
            """INSERT INTO compositions (product_id, component_id, quantity, notes)
               VALUES (?, ?, ?, ?)""",
            (product_id, component_id, quantity, notes)
        )
        self.commit()
        return self.cursor.lastrowid

    def get_product_composition(self, product_id: int) -> List[Dict]:
        """Получить состав изделия"""
        results = self.execute(
            """SELECT comp.*, c.name as component_name, c.unit, c.concrete_brand,
                      ct.name as component_type
               FROM compositions comp
               JOIN components c ON comp.component_id = c.id
               JOIN component_types ct ON c.type_id = ct.id
               WHERE comp.product_id = ?
               ORDER BY ct.name, c.name""",
            (product_id,)
        ).fetchall()
        return [dict(row) for row in results]

    def delete_composition(self, composition_id: int) -> bool:
        """Удалить комплектующее из состава"""
        self.execute("DELETE FROM compositions WHERE id = ?", (composition_id,))
        self.commit()
        return self.cursor.rowcount > 0

    # ============================================
    # PRODUCTION PLANS (Планы производства)
    # ============================================

    def create_production_plan(self, month: int, year: int, version: int,
                               version_date: str, notes: str = None) -> int:
        """
        Создать новый план производства

        Args:
            month: Месяц (1-12)
            year: Год
            version: Номер версии
            version_date: Дата создания версии (YYYY-MM-DD)
            notes: Примечания

        Returns:
            ID созданного плана
        """
        self.execute(
            """INSERT INTO production_plans (month, year, version, version_date, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (month, year, version, version_date, notes)
        )
        self.commit()
        return self.cursor.lastrowid

    def get_production_plan(self, plan_id: int) -> Optional[Dict]:
        """
        Получить план производства по ID

        Args:
            plan_id: ID плана

        Returns:
            Словарь с данными плана или None
        """
        result = self.execute(
            "SELECT * FROM production_plans WHERE id = ?",
            (plan_id,)
        ).fetchone()
        return dict(result) if result else None

    def get_all_production_plans(self) -> List[Dict]:
        """
        Получить все планы производства

        Returns:
            Список планов, отсортированный по году, месяцу и версии
        """
        results = self.execute(
            """SELECT * FROM production_plans
               ORDER BY year DESC, month DESC, version DESC"""
        ).fetchall()
        return [dict(row) for row in results]

    def get_plans_by_month_year(self, month: int, year: int) -> List[Dict]:
        """
        Получить все версии плана на заданный месяц и год

        Args:
            month: Месяц (1-12)
            year: Год

        Returns:
            Список версий плана
        """
        results = self.execute(
            """SELECT * FROM production_plans
               WHERE month = ? AND year = ?
               ORDER BY version DESC""",
            (month, year)
        ).fetchall()
        return [dict(row) for row in results]

    def get_latest_plan_version(self, month: int, year: int) -> Optional[Dict]:
        """
        Получить актуальную (последнюю) версию плана на месяц

        Args:
            month: Месяц (1-12)
            year: Год

        Returns:
            Словарь с данными последней версии или None
        """
        result = self.execute(
            """SELECT * FROM production_plans
               WHERE month = ? AND year = ?
               ORDER BY version DESC
               LIMIT 1""",
            (month, year)
        ).fetchone()
        return dict(result) if result else None

    def update_production_plan(self, plan_id: int, notes: str = None) -> bool:
        """
        Обновить план производства (только примечания)

        Args:
            plan_id: ID плана
            notes: Новые примечания

        Returns:
            True если обновление прошло успешно
        """
        if notes is None:
            return False

        self.execute(
            "UPDATE production_plans SET notes = ? WHERE id = ?",
            (notes, plan_id)
        )
        self.commit()
        return self.cursor.rowcount > 0

    def delete_production_plan(self, plan_id: int) -> bool:
        """
        Удалить план производства (также удалятся все позиции)

        Args:
            plan_id: ID плана

        Returns:
            True если удаление прошло успешно
        """
        self.execute("DELETE FROM production_plans WHERE id = ?", (plan_id,))
        self.commit()
        return self.cursor.rowcount > 0

    # ============================================
    # PRODUCTION PLAN ITEMS (Позиции плана)
    # ============================================

    def add_plan_item(self, plan_id: int, product_id: int,
                     quantity_was: int, quantity_now: int,
                     deadline_was: str = None, deadline_now: str = None,
                     notes: str = None) -> int:
        """
        Добавить позицию в план производства

        Args:
            plan_id: ID плана
            product_id: ID изделия
            quantity_was: Было (количество)
            quantity_now: Стало (количество)
            deadline_was: Срок был (YYYY-MM-DD)
            deadline_now: Срок стал (YYYY-MM-DD)
            notes: Примечания

        Returns:
            ID созданной позиции
        """
        self.execute(
            """INSERT INTO production_plan_items
               (plan_id, product_id, quantity_was, quantity_now,
                deadline_was, deadline_now, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (plan_id, product_id, quantity_was, quantity_now,
             deadline_was, deadline_now, notes)
        )
        self.commit()
        return self.cursor.lastrowid

    def get_plan_items(self, plan_id: int) -> List[Dict]:
        """
        Получить все позиции плана

        Args:
            plan_id: ID плана

        Returns:
            Список позиций с информацией об изделиях и заказчиках
        """
        results = self.execute(
            """SELECT ppi.*,
                      p.drawing_number, p.variant, p.description,
                      c.name as client_name
               FROM production_plan_items ppi
               JOIN products p ON ppi.product_id = p.id
               JOIN clients c ON p.client_id = c.id
               WHERE ppi.plan_id = ?
               ORDER BY c.name, p.drawing_number, p.variant""",
            (plan_id,)
        ).fetchall()
        return [dict(row) for row in results]

    def get_plan_item(self, item_id: int) -> Optional[Dict]:
        """
        Получить одну позицию плана

        Args:
            item_id: ID позиции

        Returns:
            Словарь с данными позиции или None
        """
        result = self.execute(
            """SELECT ppi.*,
                      p.drawing_number, p.variant, p.description,
                      c.name as client_name
               FROM production_plan_items ppi
               JOIN products p ON ppi.product_id = p.id
               JOIN clients c ON p.client_id = c.id
               WHERE ppi.id = ?""",
            (item_id,)
        ).fetchone()
        return dict(result) if result else None

    def update_plan_item(self, item_id: int,
                        quantity_was: int = None, quantity_now: int = None,
                        deadline_was: str = None, deadline_now: str = None,
                        notes: str = None) -> bool:
        """
        Обновить позицию плана

        Args:
            item_id: ID позиции
            quantity_was: Было (количество)
            quantity_now: Стало (количество)
            deadline_was: Срок был (YYYY-MM-DD)
            deadline_now: Срок стал (YYYY-MM-DD)
            notes: Примечания

        Returns:
            True если обновление прошло успешно
        """
        updates = []
        params = []

        if quantity_was is not None:
            updates.append("quantity_was = ?")
            params.append(quantity_was)
        if quantity_now is not None:
            updates.append("quantity_now = ?")
            params.append(quantity_now)
        if deadline_was is not None:
            updates.append("deadline_was = ?")
            params.append(deadline_was)
        if deadline_now is not None:
            updates.append("deadline_now = ?")
            params.append(deadline_now)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)

        if not updates:
            return False

        params.append(item_id)
        query = f"UPDATE production_plan_items SET {', '.join(updates)} WHERE id = ?"
        self.execute(query, tuple(params))
        self.commit()
        return self.cursor.rowcount > 0

    def delete_plan_item(self, item_id: int) -> bool:
        """
        Удалить позицию из плана

        Args:
            item_id: ID позиции

        Returns:
            True если удаление прошло успешно
        """
        self.execute("DELETE FROM production_plan_items WHERE id = ?", (item_id,))
        self.commit()
        return self.cursor.rowcount > 0

    # ============================================
    # COMPONENT PRICES (Цены на комплектующие)
    # ============================================

    def add_component_price(self, component_id: int, price: float,
                           currency: str = 'RUB', valid_from: str = None,
                           notes: str = None) -> int:
        """
        Добавить цену на комплектующее

        Args:
            component_id: ID комплектующего
            price: Цена за единицу
            currency: Валюта (по умолчанию RUB)
            valid_from: Дата начала действия (YYYY-MM-DD, по умолчанию сегодня)
            notes: Примечания

        Returns:
            ID созданной записи о цене
        """
        if valid_from is None:
            valid_from = date.today().isoformat()

        self.execute(
            """INSERT INTO component_prices
               (component_id, price, currency, valid_from, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (component_id, price, currency, valid_from, notes)
        )
        self.commit()
        return self.cursor.lastrowid

    def get_component_price_current(self, component_id: int) -> Optional[Dict]:
        """
        Получить актуальную цену комплектующего

        Args:
            component_id: ID комплектующего

        Returns:
            Словарь с данными цены или None
        """
        result = self.execute(
            """SELECT cp.*, c.name as component_name, c.unit
               FROM component_prices cp
               JOIN components c ON cp.component_id = c.id
               WHERE cp.component_id = ? AND cp.valid_from <= date('now')
               ORDER BY cp.valid_from DESC
               LIMIT 1""",
            (component_id,)
        ).fetchone()
        return dict(result) if result else None

    def get_component_prices_history(self, component_id: int) -> List[Dict]:
        """
        Получить историю цен комплектующего

        Args:
            component_id: ID комплектующего

        Returns:
            Список цен, отсортированный по дате
        """
        results = self.execute(
            """SELECT cp.*, c.name as component_name, c.unit
               FROM component_prices cp
               JOIN components c ON cp.component_id = c.id
               WHERE cp.component_id = ?
               ORDER BY cp.valid_from DESC""",
            (component_id,)
        ).fetchall()
        return [dict(row) for row in results]

    def import_prices_from_dict(self, prices_data: List[Dict]) -> Tuple[int, List[str]]:
        """
        Импортировать цены из списка словарей

        Args:
            prices_data: Список словарей с ключами:
                        - component_id: ID комплектующего
                        - price: Цена
                        - currency: Валюта (опционально)
                        - valid_from: Дата начала действия (опционально)
                        - notes: Примечания (опционально)

        Returns:
            Кортеж (количество добавленных цен, список ошибок)
        """
        count = 0
        errors = []

        for i, price_data in enumerate(prices_data):
            try:
                component_id = price_data['component_id']
                price = price_data['price']
                currency = price_data.get('currency', 'RUB')
                valid_from = price_data.get('valid_from', date.today().isoformat())
                notes = price_data.get('notes', None)

                self.add_component_price(component_id, price, currency, valid_from, notes)
                count += 1
            except Exception as e:
                errors.append(f"Строка {i+1}: {str(e)}")

        return count, errors


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def init_database(db_path: str = "data/productdb.sqlite", schema_path: str = "schema.sql"):
    """
    Инициализировать базу данных из SQL схемы

    Args:
        db_path: Путь к файлу БД
        schema_path: Путь к файлу схемы
    """
    import os

    # Создать директорию data если не существует
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Прочитать SQL схему
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Создать БД
    conn = sqlite3.connect(db_path)
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()

    print(f"✅ База данных инициализирована: {db_path}")


if __name__ == "__main__":
    # Тестирование модуля
    print("🔧 Тестирование database.py...")

    # Инициализация БД
    init_database()

    # Тестирование функций
    with Database() as db:
        # Тест: получить все планы
        plans = db.get_all_production_plans()
        print(f"\n📋 Всего планов в БД: {len(plans)}")

        if plans:
            plan = plans[0]
            print(f"   План ID={plan['id']}: {plan['month']}/{plan['year']} v{plan['version']}")

            # Тест: получить позиции плана
            items = db.get_plan_items(plan['id'])
            print(f"   Позиций в плане: {len(items)}")

            for item in items:
                print(f"   - {item['client_name']}: {item['drawing_number']} {item['variant']}")
                print(f"     Было: {item['quantity_was']}, Стало: {item['quantity_now']}")

        # Тест: получить актуальную цену
        components = db.get_all_components()
        if components:
            comp = components[0]
            price = db.get_component_price_current(comp['id'])
            if price:
                print(f"\n💰 Цена {comp['name']}: {price['price']} {price['currency']}")

    print("\n✅ Тестирование завершено!")
