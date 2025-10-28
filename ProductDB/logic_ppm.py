"""
ProductDB - PPM Business Logic Module
Бизнес-логика модуля ППМ (План Производства на Месяц)
"""

from typing import Dict, List, Optional, Tuple
from datetime import date, datetime
from database import Database


# ============================================
# РАСЧЕТ ПОТРЕБНОСТИ В МАТЕРИАЛАХ
# ============================================

def calculate_material_requirements(plan_id: int, db: Database) -> Dict:
    """
    Рассчитать потребность в материалах и комплектующих для плана

    Алгоритм:
    1. Получить все позиции плана
    2. Для каждой позиции получить комплектацию изделия
    3. Умножить quantity_now на количество каждого комплектующего
    4. Суммировать одинаковые комплектующие
    5. Рассчитать вес бетона по маркам отдельно

    Args:
        plan_id: ID плана производства
        db: Объект подключения к БД

    Returns:
        Словарь с результатами расчета:
        {
            'plan_id': int,
            'plan_info': {month, year, version, ...},
            'requirements': [
                {
                    'component_id': int,
                    'component_name': str,
                    'component_type': str,
                    'unit': str,
                    'quantity': float,
                    'concrete_brand': str or None
                },
                ...
            ],
            'concrete_by_brand': {
                'M20': 15050.0,
                'M25': 10000.0,
                ...
            },
            'total_products': int  # Общее количество изделий
        }
    """
    # Получить информацию о плане
    plan = db.get_production_plan(plan_id)
    if not plan:
        raise ValueError(f"План с ID {plan_id} не найден")

    # Получить все позиции плана
    plan_items = db.get_plan_items(plan_id)

    if not plan_items:
        return {
            'plan_id': plan_id,
            'plan_info': plan,
            'requirements': [],
            'concrete_by_brand': {},
            'total_products': 0
        }

    # Словарь для накопления требований: {component_id: quantity}
    requirements_map = {}
    # Словарь для накопления бетона по маркам: {brand: weight_kg}
    concrete_by_brand = {}
    # Счетчик изделий
    total_products = 0

    # Обработать каждую позицию плана
    for item in plan_items:
        product_id = item['product_id']
        quantity_now = item['quantity_now']

        if quantity_now <= 0:
            continue  # Пропустить отмененные заказы

        total_products += quantity_now

        # Получить комплектацию изделия
        composition = db.get_product_composition(product_id)

        # Обработать каждый компонент в составе
        for comp in composition:
            component_id = comp['component_id']
            quantity_per_unit = comp['quantity']
            total_quantity = quantity_per_unit * quantity_now

            # Накопить количество
            if component_id in requirements_map:
                requirements_map[component_id]['quantity'] += total_quantity
            else:
                requirements_map[component_id] = {
                    'component_id': component_id,
                    'component_name': comp['component_name'],
                    'component_type': comp['component_type'],
                    'unit': comp['unit'],
                    'quantity': total_quantity,
                    'concrete_brand': comp['concrete_brand']
                }

            # Если это бетон - накопить по маркам
            if comp['concrete_brand']:
                brand = comp['concrete_brand']
                if brand in concrete_by_brand:
                    concrete_by_brand[brand] += total_quantity
                else:
                    concrete_by_brand[brand] = total_quantity

    # Преобразовать словарь в список и отсортировать
    requirements = list(requirements_map.values())
    requirements.sort(key=lambda x: (x['component_type'], x['component_name']))

    return {
        'plan_id': plan_id,
        'plan_info': plan,
        'requirements': requirements,
        'concrete_by_brand': concrete_by_brand,
        'total_products': total_products
    }


# ============================================
# РАСЧЕТ ЗАТРАТ
# ============================================

def calculate_costs(material_requirements: Dict, db: Database,
                   include_missing: bool = True) -> Dict:
    """
    Рассчитать затраты на материалы

    Args:
        material_requirements: Результат функции calculate_material_requirements
        db: Объект подключения к БД
        include_missing: Включать ли компоненты без цены (с ценой 0)

    Returns:
        Словарь с результатами расчета:
        {
            'requirements_with_prices': [
                {
                    'component_id': int,
                    'component_name': str,
                    'component_type': str,
                    'unit': str,
                    'quantity': float,
                    'price': float,
                    'currency': str,
                    'total_cost': float,
                    'has_price': bool
                },
                ...
            ],
            'total_cost': float,
            'currency': str,
            'components_with_price': int,
            'components_without_price': int
        }
    """
    requirements = material_requirements['requirements']
    results = []
    total_cost = 0.0
    currency = 'RUB'
    components_with_price = 0
    components_without_price = 0

    for req in requirements:
        component_id = req['component_id']

        # Получить актуальную цену
        price_info = db.get_component_price_current(component_id)

        if price_info:
            price = price_info['price']
            currency = price_info['currency']
            has_price = True
            components_with_price += 1
        else:
            price = 0.0
            has_price = False
            components_without_price += 1

        total_cost_item = req['quantity'] * price
        total_cost += total_cost_item

        item = {
            'component_id': component_id,
            'component_name': req['component_name'],
            'component_type': req['component_type'],
            'unit': req['unit'],
            'quantity': req['quantity'],
            'price': price,
            'currency': currency,
            'total_cost': total_cost_item,
            'has_price': has_price
        }

        # Добавить в результаты
        if include_missing or has_price:
            results.append(item)

    return {
        'requirements_with_prices': results,
        'total_cost': total_cost,
        'currency': currency,
        'components_with_price': components_with_price,
        'components_without_price': components_without_price
    }


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def get_active_plan(month: int, year: int, db: Database) -> Optional[Dict]:
    """
    Получить актуальную версию плана на месяц

    Args:
        month: Месяц (1-12)
        year: Год
        db: Объект подключения к БД

    Returns:
        Словарь с данными плана или None
    """
    return db.get_latest_plan_version(month, year)


def compare_plan_versions(plan_id_1: int, plan_id_2: int, db: Database) -> Dict:
    """
    Сравнить две версии плана

    Args:
        plan_id_1: ID первой версии (обычно старая)
        plan_id_2: ID второй версии (обычно новая)
        db: Объект подключения к БД

    Returns:
        Словарь с результатами сравнения:
        {
            'plan_1': {...},
            'plan_2': {...},
            'added_items': [...],      # Новые позиции
            'removed_items': [...],    # Удаленные позиции
            'modified_items': [...],   # Измененные позиции
            'unchanged_items': [...]   # Неизмененные позиции
        }
    """
    plan1 = db.get_production_plan(plan_id_1)
    plan2 = db.get_production_plan(plan_id_2)

    if not plan1 or not plan2:
        raise ValueError("Один или оба плана не найдены")

    items1 = db.get_plan_items(plan_id_1)
    items2 = db.get_plan_items(plan_id_2)

    # Создать словари для быстрого поиска: {product_id: item}
    items1_map = {item['product_id']: item for item in items1}
    items2_map = {item['product_id']: item for item in items2}

    added_items = []
    removed_items = []
    modified_items = []
    unchanged_items = []

    # Найти добавленные и измененные позиции
    for product_id, item2 in items2_map.items():
        if product_id not in items1_map:
            # Новая позиция
            added_items.append(item2)
        else:
            # Существующая позиция - проверить изменения
            item1 = items1_map[product_id]
            if (item1['quantity_now'] != item2['quantity_now'] or
                item1['deadline_now'] != item2['deadline_now']):
                # Изменена
                modified_items.append({
                    'old': item1,
                    'new': item2
                })
            else:
                # Не изменена
                unchanged_items.append(item2)

    # Найти удаленные позиции
    for product_id, item1 in items1_map.items():
        if product_id not in items2_map:
            removed_items.append(item1)

    return {
        'plan_1': plan1,
        'plan_2': plan2,
        'added_items': added_items,
        'removed_items': removed_items,
        'modified_items': modified_items,
        'unchanged_items': unchanged_items
    }


def format_material_list(requirements: List[Dict]) -> str:
    """
    Форматировать список материалов для отображения

    Args:
        requirements: Список требований из calculate_material_requirements

    Returns:
        Отформатированная строка
    """
    if not requirements:
        return "Материалы не требуются"

    lines = []
    lines.append("СПИСОК МАТЕРИАЛОВ")
    lines.append("=" * 60)

    current_type = None
    for req in requirements:
        # Заголовок типа
        if req['component_type'] != current_type:
            current_type = req['component_type']
            lines.append(f"\n{current_type.upper()}:")

        # Строка материала
        name = req['component_name']
        quantity = req['quantity']
        unit = req['unit']

        if req['concrete_brand']:
            line = f"  • {name} ({req['concrete_brand']}): {quantity:.2f} {unit}"
        else:
            line = f"  • {name}: {quantity:.2f} {unit}"

        lines.append(line)

    return "\n".join(lines)


def group_by_component_type(requirements: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Группировать требования по типу комплектующих

    Args:
        requirements: Список требований из calculate_material_requirements

    Returns:
        Словарь {type_name: [requirements]}
    """
    grouped = {}

    for req in requirements:
        comp_type = req['component_type']
        if comp_type not in grouped:
            grouped[comp_type] = []
        grouped[comp_type].append(req)

    return grouped


# ============================================
# ВАЛИДАЦИЯ
# ============================================

def validate_plan_data(month: int, year: int, version: int) -> Tuple[bool, Optional[str]]:
    """
    Проверить корректность данных плана

    Args:
        month: Месяц (1-12)
        year: Год
        version: Версия

    Returns:
        (успех, сообщение об ошибке)
    """
    if month < 1 or month > 12:
        return False, f"Месяц должен быть от 1 до 12, получено: {month}"

    if year < 2020 or year > 2100:
        return False, f"Год должен быть от 2020 до 2100, получено: {year}"

    if version < 1:
        return False, f"Версия должна быть >= 1, получено: {version}"

    return True, None


def validate_plan_item_data(product_id: int, quantity: int,
                           deadline: str) -> Tuple[bool, Optional[str]]:
    """
    Проверить корректность данных позиции плана

    Args:
        product_id: ID изделия
        quantity: Количество
        deadline: Срок (YYYY-MM-DD)

    Returns:
        (успех, сообщение об ошибке)
    """
    if product_id < 1:
        return False, f"ID изделия должен быть >= 1, получено: {product_id}"

    if quantity < 0:
        return False, f"Количество должно быть >= 0, получено: {quantity}"

    # Проверить формат даты
    try:
        datetime.strptime(deadline, '%Y-%m-%d')
    except ValueError:
        return False, f"Неверный формат даты: {deadline}. Ожидается YYYY-MM-DD"

    return True, None


# ============================================
# ТЕСТИРОВАНИЕ
# ============================================

if __name__ == "__main__":
    print("🔧 Тестирование logic_ppm.py...")

    with Database() as db:
        # Получить все планы
        plans = db.get_all_production_plans()
        if not plans:
            print("❌ В БД нет планов для тестирования")
            print("💡 Запустите сначала database.py для инициализации БД")
            exit(1)

        plan = plans[0]
        plan_id = plan['id']

        print(f"\n📋 Тестирование плана ID={plan_id}: {plan['month']}/{plan['year']} v{plan['version']}")

        # Тест 1: Расчет потребности
        print("\n1️⃣ Расчет потребности в материалах...")
        requirements = calculate_material_requirements(plan_id, db)

        print(f"   ✅ Всего изделий: {requirements['total_products']}")
        print(f"   ✅ Видов материалов: {len(requirements['requirements'])}")

        # Показать бетон по маркам
        if requirements['concrete_by_brand']:
            print("\n   Бетон по маркам:")
            for brand, weight in requirements['concrete_by_brand'].items():
                print(f"   - {brand}: {weight:.2f} кг")

        # Тест 2: Расчет затрат
        print("\n2️⃣ Расчет затрат...")
        costs = calculate_costs(requirements, db)

        print(f"   ✅ Общая стоимость: {costs['total_cost']:.2f} {costs['currency']}")
        print(f"   ✅ С ценой: {costs['components_with_price']} компонентов")
        print(f"   ⚠️  Без цены: {costs['components_without_price']} компонентов")

        # Тест 3: Форматирование списка
        print("\n3️⃣ Форматированный список материалов:")
        formatted = format_material_list(requirements['requirements'])
        print(formatted)

        # Тест 4: Группировка по типу
        print("\n4️⃣ Группировка по типу комплектующих:")
        grouped = group_by_component_type(requirements['requirements'])
        for comp_type, items in grouped.items():
            print(f"   {comp_type}: {len(items)} позиций")

        # Тест 5: Валидация
        print("\n5️⃣ Тестирование валидации...")
        valid, error = validate_plan_data(11, 2025, 1)
        print(f"   {'✅' if valid else '❌'} Валидация плана (11, 2025, v1): {error or 'OK'}")

        valid, error = validate_plan_data(13, 2025, 1)
        print(f"   {'✅' if not valid else '❌'} Валидация плана (13, 2025, v1): {error or 'OK'}")

        valid, error = validate_plan_item_data(1, 100, '2025-11-30')
        print(f"   {'✅' if valid else '❌'} Валидация позиции: {error or 'OK'}")

    print("\n✅ Тестирование завершено!")
