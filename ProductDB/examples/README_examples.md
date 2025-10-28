# Примеры файлов ProductDB

## 📄 prices_example.json

Пример файла для импорта цен на комплектующие в формате JSON.

**Формат:**
```json
[
    {
        "component_id": 1,           // ID комплектующего из таблицы components
        "price": 15.50,              // Цена за единицу
        "currency": "RUB",           // Валюта (по умолчанию RUB)
        "valid_from": "2025-01-01",  // Дата начала действия цены (YYYY-MM-DD)
        "notes": "Примечание"        // Опциональное примечание
    }
]
```

**Использование:**
```python
from database import Database
from export_ppm import import_prices_from_json

with Database() as db:
    count, errors = import_prices_from_json('examples/prices_example.json', db)
    print(f"Импортировано {count} цен")
    if errors:
        print(f"Ошибки: {errors}")
```

---

## 📊 prices_example.xlsx

Пример файла для импорта цен в формате Excel.

**Формат таблицы:**

| ID комплектующего | Цена | Валюта | Дата начала действия | Примечания |
|-------------------|------|--------|---------------------|------------|
| 1 | 15.50 | RUB | 2025-01-01 | Бетон M20 |
| 2 | 18.00 | RUB | 2025-01-01 | Бетон M25 |
| ... | ... | ... | ... | ... |

**Использование:**
```python
from database import Database
from export_ppm import import_prices_from_excel

with Database() as db:
    count, errors = import_prices_from_excel('examples/prices_example.xlsx', db)
    print(f"Импортировано {count} цен")
```

---

## 📋 PPM_template.xlsx

Шаблон для экспорта ППМ для директора (должен быть создан вручную в Excel).

**Рекомендуемая структура:**
- Ячейка B2: Месяц
- Ячейка D2: Год
- Ячейка F2: Версия
- Строка 5 и далее: Таблица с позициями

**Файл конфигурации (PPM_config.json):**
```json
{
    "month_cell": "B2",
    "year_cell": "D2",
    "version_cell": "F2",
    "items_start_row": 5,
    "columns": {
        "number": "A",
        "client": "B",
        "drawing": "C",
        "variant": "D",
        "quantity_was": "E",
        "quantity_now": "F",
        "deadline_was": "G",
        "deadline_now": "H",
        "notes": "I"
    }
}
```

---

## 💡 Советы

1. **JSON формат** удобен для программного управления ценами
2. **Excel формат** удобен для ручного редактирования
3. Убедитесь, что `component_id` существует в базе данных
4. Дата должна быть в формате YYYY-MM-DD
5. При импорте из Excel первая строка считается заголовком и пропускается
