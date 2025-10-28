# ProductDB - ERP система для производства огнеупорных изделий

**Статус:** 🚧 В разработке
**Версия:** 0.1.0 (MVP - Модуль ППМ)
**Последнее обновление:** 28.10.2025

---

## 📋 Описание

ProductDB - это модульная ERP система для управления производством огнеупорных изделий. Система позволяет:

- 📦 Управлять каталогом изделий и их комплектацией
- 👥 Вести базу заказчиков
- 📅 Планировать производство с версионированием (модуль ППМ)
- 🧮 Рассчитывать потребность в материалах и комплектующих
- 💰 Управлять ценами и рассчитывать затраты
- 📊 Экспортировать отчёты в Excel

---

## 🎯 Модуль ППМ (План Производства на Месяц)

### Основные возможности

✅ **Создание планов с версионированием**
- Один план на месяц с несколькими версиями (v1, v2, v3...)
- Последняя версия = актуальная, остальные = архив

✅ **Отслеживание изменений "было/стало"**
- Для каждой позиции фиксируется: количество было → стало
- Сроки: deadline_was → deadline_now
- Примечания к изменениям

✅ **Расчёт потребности в материалах**
- Автоматический расчёт по комплектации изделий
- Суммирование одинаковых комплектующих
- Отдельный учёт бетона по маркам (M20, M25, M28...)

✅ **Расчёт затрат**
- Умножение количества на актуальные цены
- История цен с датами начала действия
- Отчёты с ценами и без

✅ **Экспорт отчётов в Excel**
- Отчёт для снабженца (список материалов + цены)
- ППМ для директора (шаблонный документ для подписи)
- Красивое форматирование с группировкой по типам

---

## 🗂️ Структура проекта

```
ProductDB/
├── data/                          # База данных
│   └── productdb.sqlite
├── templates/                     # Шаблоны Excel
│   ├── PPM_template.xlsx
│   └── PPM_config.json
├── reports/                       # Экспортированные отчёты
│   ├── supply/                    # Отчёты для снабженца
│   └── plans/                     # ППМ для директора
├── examples/                      # Примеры файлов
│   ├── prices_example.json
│   ├── prices_example.xlsx
│   └── README_examples.md
├── schema.sql                     # Схема базы данных
├── database.py                    # Функции работы с БД
├── logic_ppm.py                   # Бизнес-логика расчётов
├── export_ppm.py                  # Экспорт в Excel
├── create_examples.py             # Создание примеров
├── DESIGN_PPM.md                  # Техническая документация
├── TODO.md                        # План работ
└── README.md                      # Этот файл
```

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install openpyxl
```

### 2. Инициализация базы данных

```bash
cd ProductDB
python3 database.py
```

Это создаст файл `data/productdb.sqlite` с тестовыми данными.

### 3. Тестирование расчётов

```bash
python3 logic_ppm.py
```

Вывод:
```
📋 Тестирование плана ID=1: 11/2025 v1
✅ Всего изделий: 150
✅ Видов материалов: 5

Бетон по маркам:
- M20: 15050.00 кг
- M25: 10000.00 кг

✅ Общая стоимость: 482775.00 RUB
```

### 4. Экспорт отчётов

```bash
python3 export_ppm.py
```

Создаст файлы:
- `reports/supply/Потребность_материалы_2025-11_v1.xlsx`
- `reports/plans/ППМ_2025-11_v1.xlsx`

---

## 📚 Использование

### Работа с базой данных

```python
from database import Database

# Контекстный менеджер (рекомендуется)
with Database() as db:
    # Создать план
    plan_id = db.create_production_plan(
        month=11,
        year=2025,
        version=1,
        version_date='2025-11-01',
        notes='Первоначальный план'
    )

    # Добавить позицию
    item_id = db.add_plan_item(
        plan_id=plan_id,
        product_id=1,
        quantity_was=0,
        quantity_now=100,
        deadline_now='2025-11-30',
        notes='Новый заказ'
    )

    # Получить все позиции плана
    items = db.get_plan_items(plan_id)
    for item in items:
        print(f"{item['client_name']}: {item['drawing_number']} - {item['quantity_now']} шт")
```

### Расчёты

```python
from database import Database
from logic_ppm import calculate_material_requirements, calculate_costs

with Database() as db:
    # Рассчитать потребность
    requirements = calculate_material_requirements(plan_id=1, db=db)

    print(f"Всего изделий: {requirements['total_products']}")
    print(f"Видов материалов: {len(requirements['requirements'])}")

    # Бетон по маркам
    for brand, weight in requirements['concrete_by_brand'].items():
        print(f"{brand}: {weight:.2f} кг")

    # Рассчитать затраты
    costs = calculate_costs(requirements, db)
    print(f"Общая стоимость: {costs['total_cost']:.2f} {costs['currency']}")
```

### Экспорт отчётов

```python
from database import Database
from export_ppm import export_supply_report, export_ppm_for_director

with Database() as db:
    # Отчёт для снабженца (с ценами)
    filepath = export_supply_report(
        plan_id=1,
        db=db,
        include_prices=True
    )
    print(f"Отчёт создан: {filepath}")

    # ППМ для директора
    filepath = export_ppm_for_director(
        plan_id=1,
        db=db,
        template_path='templates/PPM_template.xlsx',
        config_path='templates/PPM_config.json'
    )
    print(f"ППМ создан: {filepath}")
```

### Импорт цен

```python
from database import Database
from export_ppm import import_prices_from_json, import_prices_from_excel

with Database() as db:
    # Из JSON
    count, errors = import_prices_from_json('examples/prices_example.json', db)
    print(f"Импортировано {count} цен")

    # Из Excel
    count, errors = import_prices_from_excel('examples/prices_example.xlsx', db)
    print(f"Импортировано {count} цен")

    if errors:
        for error in errors:
            print(f"Ошибка: {error}")
```

---

## 🗄️ База данных

### Основные таблицы

**clients** - Заказчики
- `id`, `name`, `contact_info`, `notes`

**products** - Изделия
- `id`, `client_id`, `drawing_number`, `variant`, `description`
- Уникальность: (client_id, drawing_number, variant)
- Пример: PB 35.126 R2-B15-НТ

**components** - Комплектующие
- `id`, `type_id`, `name`, `unit`, `concrete_brand`
- Типы: Бетон, Закладная деталь, Крепеж, Картон...

**compositions** - Комплектация изделий
- `id`, `product_id`, `component_id`, `quantity`
- Связь многие-ко-многим между изделиями и комплектующими

**production_plans** - Планы производства
- `id`, `month`, `year`, `version`, `version_date`, `notes`
- Уникальность: (month, year, version)

**production_plan_items** - Позиции плана
- `id`, `plan_id`, `product_id`
- `quantity_was`, `quantity_now` - было/стало
- `deadline_was`, `deadline_now` - сроки

**component_prices** - Цены на комплектующие
- `id`, `component_id`, `price`, `currency`, `valid_from`
- История цен с датами начала действия

---

## 🔧 Разработка

### Текущий статус (v0.1.0)

**Выполнено:**
- ✅ Проектирование архитектуры (DESIGN_PPM.md)
- ✅ Схема базы данных (10 таблиц + триггеры + индексы)
- ✅ Модуль database.py (~750 строк, 18+ функций)
- ✅ Модуль logic_ppm.py (~550 строк, расчёты + валидация)
- ✅ Модуль export_ppm.py (~500 строк, Excel экспорт/импорт)
- ✅ Тестирование всех функций
- ✅ Примеры файлов и шаблоны
- ✅ Документация

**Осталось:**
- ⏳ GUI (gui_ppm.py, ~900 строк)
- ⏳ Интеграция с main.py
- ⏳ Полное тестирование с GUI
- ⏳ Компиляция в исполняемый файл

### План работ

Подробный план работ с оценками времени см. в [TODO.md](TODO.md)

**Приоритеты:**
1. GUI базовый (создание плана, просмотр) - 3-4 часа
2. GUI полный (редактирование, отчёты) - 2-3 часа
3. Интеграция и тестирование - 2 часа
4. Полировка и документация - 1 час

**Итого:** ~8-10 часов до завершения MVP

---

## 📊 Примеры отчётов

### Отчёт для снабженца

```
ПОТРЕБНОСТЬ В МАТЕРИАЛАХ
План: Ноябрь 2025 (версия 1)

№ | Наименование              | Ед.  | Количество | Цена, руб. | Сумма, руб.
--|---------------------------|------|------------|------------|-------------
  | БЕТОН
1 | Бетон M20 (M20)          | кг   | 15050.00   | 15.50      | 233275.00
2 | Бетон M25 (M25)          | кг   | 10000.00   | 18.00      | 180000.00
  | ЗАКЛАДНАЯ ДЕТАЛЬ
3 | Закладная деталь ZD-100  | шт   | 250.00     | 250.00     | 62500.00
  | КАРТОН
4 | Картон асбестовый        | м2   | 25.00      | 120.00     | 3000.00
  | КРЕПЕЖ
5 | Болт М12                 | шт   | 800.00     | 5.00       | 4000.00
--|---------------------------|------|------------|------------|-------------
                                                ИТОГО:        482775.00

БЕТОН ПО МАРКАМ:
  M20: 15050.00 кг
  M25: 10000.00 кг
```

### ППМ для директора

Заполняется шаблон Excel с:
- Заголовком с месяцем, годом, версией
- Таблицей позиций (заказчик, чертёж, вариант, количество, сроки)
- Полями для подписи директора

---

## 🤝 Вклад в разработку

Этот проект разрабатывается в тесном сотрудничестве человека и ИИ.

**Процесс разработки:**
1. Обсуждение требований и бизнес-логики
2. Проектирование архитектуры (DESIGN_PPM.md)
3. Итеративная разработка модулей
4. Тестирование на каждом этапе
5. Документирование

---

## 📄 Лицензия

Проект разрабатывается для внутреннего использования.

---

## 📞 Контакты

Вопросы и предложения направляйте разработчику проекта.

---

## 🔗 Связанные документы

- [DESIGN_PPM.md](DESIGN_PPM.md) - Полная техническая документация
- [TODO.md](TODO.md) - План работ и задачи
- [examples/README_examples.md](examples/README_examples.md) - Описание примеров файлов

---

**Сделано с ❤️ и 🤖 Claude Code**
