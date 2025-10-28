-- ============================================
-- ProductDB: ERP система для производства огнеупорных изделий
-- ============================================

-- ============================================
-- 1. ТАБЛИЦА: clients (Заказчики)
-- ============================================
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    contact_info TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. ТАБЛИЦА: products (Изделия)
-- ============================================
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    drawing_number TEXT NOT NULL,           -- Номер чертежа (PB 35.126, SB 651, PBS 15.126R)
    variant TEXT NOT NULL,                  -- Вариант (R2-B15-НТ, B2-ЗС, B1-КО)
    description TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE RESTRICT,
    UNIQUE(client_id, drawing_number, variant)
);

CREATE INDEX IF NOT EXISTS idx_products_client ON products(client_id);
CREATE INDEX IF NOT EXISTS idx_products_drawing ON products(drawing_number);

-- ============================================
-- 3. ТАБЛИЦА: component_types (Типы комплектующих)
-- ============================================
CREATE TABLE IF NOT EXISTS component_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- Бетон, Закладная деталь, Крепеж, Картон, etc.
    unit TEXT NOT NULL,                     -- кг, шт, м2, etc.
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 4. ТАБЛИЦА: components (Комплектующие)
-- ============================================
CREATE TABLE IF NOT EXISTS components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_id INTEGER NOT NULL,
    name TEXT NOT NULL UNIQUE,
    unit TEXT NOT NULL,
    concrete_brand TEXT,                    -- Марка бетона (M20, M25, etc.) - только для типа "Бетон"
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (type_id) REFERENCES component_types(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_components_type ON components(type_id);

-- ============================================
-- 5. ТАБЛИЦА: compositions (Комплектация изделий)
-- ============================================
CREATE TABLE IF NOT EXISTS compositions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    component_id INTEGER NOT NULL,
    quantity REAL NOT NULL,                 -- Количество на 1 изделие
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (quantity > 0),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE RESTRICT,
    UNIQUE(product_id, component_id)
);

CREATE INDEX IF NOT EXISTS idx_compositions_product ON compositions(product_id);
CREATE INDEX IF NOT EXISTS idx_compositions_component ON compositions(component_id);

-- ============================================
-- 6. ТАБЛИЦА: concrete_weights (Вес бетона по маркам)
-- ============================================
CREATE TABLE IF NOT EXISTS concrete_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    brand TEXT NOT NULL,                    -- M20, M25, M28, etc.
    weight_kg REAL NOT NULL,                -- Вес в кг
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (weight_kg > 0),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(product_id, brand)
);

CREATE INDEX IF NOT EXISTS idx_concrete_weights_product ON concrete_weights(product_id);

-- ============================================
-- 7. ТАБЛИЦА: concrete_brands (Справочник марок бетона)
-- ============================================
CREATE TABLE IF NOT EXISTS concrete_brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- M20, M25, M28, etc.
    description TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 8. ТАБЛИЦА: production_plans (Планы производства)
-- ============================================
CREATE TABLE IF NOT EXISTS production_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month INTEGER NOT NULL,                 -- Месяц (1-12)
    year INTEGER NOT NULL,                  -- Год (2025...)
    version INTEGER NOT NULL,               -- Номер версии (1, 2, 3...)
    version_date DATE NOT NULL,             -- Дата создания версии
    notes TEXT,                             -- Общие примечания к плану
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (month >= 1 AND month <= 12),
    CHECK (year >= 2020),
    CHECK (version >= 1),
    UNIQUE(month, year, version)
);

CREATE INDEX IF NOT EXISTS idx_plans_month_year ON production_plans(month, year);
CREATE INDEX IF NOT EXISTS idx_plans_version ON production_plans(version);

-- ============================================
-- 9. ТАБЛИЦА: production_plan_items (Позиции плана)
-- ============================================
CREATE TABLE IF NOT EXISTS production_plan_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity_was INTEGER DEFAULT 0,         -- Было (количество)
    quantity_now INTEGER NOT NULL,          -- Стало (количество)
    deadline_was DATE,                      -- Срок был
    deadline_now DATE NOT NULL,             -- Срок стал
    notes TEXT,                             -- Примечания к позиции
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (quantity_was >= 0),
    CHECK (quantity_now >= 0),
    FOREIGN KEY (plan_id) REFERENCES production_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_plan_items_plan ON production_plan_items(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_items_product ON production_plan_items(product_id);

-- ============================================
-- 10. ТАБЛИЦА: component_prices (Цены на комплектующие)
-- ============================================
CREATE TABLE IF NOT EXISTS component_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_id INTEGER NOT NULL,
    price REAL NOT NULL,
    currency TEXT DEFAULT 'RUB',
    valid_from DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (price >= 0),
    FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_prices_component ON component_prices(component_id);
CREATE INDEX IF NOT EXISTS idx_prices_date ON component_prices(valid_from);

-- ============================================
-- ТРИГГЕРЫ: Автообновление updated_at
-- ============================================

CREATE TRIGGER IF NOT EXISTS update_clients_timestamp
AFTER UPDATE ON clients
FOR EACH ROW
BEGIN
    UPDATE clients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_products_timestamp
AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_component_types_timestamp
AFTER UPDATE ON component_types
FOR EACH ROW
BEGIN
    UPDATE component_types SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_components_timestamp
AFTER UPDATE ON components
FOR EACH ROW
BEGIN
    UPDATE components SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_compositions_timestamp
AFTER UPDATE ON compositions
FOR EACH ROW
BEGIN
    UPDATE compositions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_concrete_weights_timestamp
AFTER UPDATE ON concrete_weights
FOR EACH ROW
BEGIN
    UPDATE concrete_weights SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_production_plans_timestamp
AFTER UPDATE ON production_plans
FOR EACH ROW
BEGIN
    UPDATE production_plans SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_production_plan_items_timestamp
AFTER UPDATE ON production_plan_items
FOR EACH ROW
BEGIN
    UPDATE production_plan_items SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_component_prices_timestamp
AFTER UPDATE ON component_prices
FOR EACH ROW
BEGIN
    UPDATE component_prices SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================
-- ТЕСТОВЫЕ ДАННЫЕ
-- ============================================

-- Заказчики
INSERT OR IGNORE INTO clients (id, name) VALUES
    (1, 'ООО "Металлургия"'),
    (2, 'АО "Сталевар"');

-- Типы комплектующих
INSERT OR IGNORE INTO component_types (id, name, unit) VALUES
    (1, 'Бетон', 'кг'),
    (2, 'Закладная деталь', 'шт'),
    (3, 'Крепеж', 'шт'),
    (4, 'Картон', 'м2');

-- Марки бетона
INSERT OR IGNORE INTO concrete_brands (name) VALUES
    ('M20'), ('M25'), ('M28');

-- Комплектующие
INSERT OR IGNORE INTO components (id, type_id, name, unit, concrete_brand) VALUES
    (1, 1, 'Бетон M20', 'кг', 'M20'),
    (2, 1, 'Бетон M25', 'кг', 'M25'),
    (3, 2, 'Закладная деталь ZD-100', 'шт', NULL),
    (4, 3, 'Болт М12', 'шт', NULL),
    (5, 4, 'Картон асбестовый', 'м2', NULL);

-- Изделия
INSERT OR IGNORE INTO products (id, client_id, drawing_number, variant, description) VALUES
    (1, 1, 'PB 35.126', 'R2-B15-НТ', 'Плита блока'),
    (2, 1, 'SB 651', 'B2-ЗС', 'Стенка блока'),
    (3, 2, 'PBS 15.126R', 'B1-КО', 'Плита боковая секции');

-- Комплектация изделий
INSERT OR IGNORE INTO compositions (product_id, component_id, quantity) VALUES
    (1, 1, 150.5),   -- PB 35.126 R2-B15-НТ: 150.5 кг бетона M20
    (1, 3, 2),       -- PB 35.126 R2-B15-НТ: 2 шт закладных
    (1, 4, 8),       -- PB 35.126 R2-B15-НТ: 8 шт болтов
    (2, 2, 200.0),   -- SB 651 B2-ЗС: 200 кг бетона M25
    (2, 3, 1),       -- SB 651 B2-ЗС: 1 шт закладная
    (2, 5, 0.5);     -- SB 651 B2-ЗС: 0.5 м2 картона

-- Вес бетона по маркам
INSERT OR IGNORE INTO concrete_weights (product_id, brand, weight_kg) VALUES
    (1, 'M20', 150.5),
    (2, 'M25', 200.0);

-- Тестовый план производства
INSERT OR IGNORE INTO production_plans (id, month, year, version, version_date, notes) VALUES
    (1, 11, 2025, 1, '2025-11-01', 'Первоначальный план на ноябрь 2025');

-- Тестовые позиции плана
INSERT OR IGNORE INTO production_plan_items (plan_id, product_id, quantity_was, quantity_now, deadline_was, deadline_now, notes) VALUES
    (1, 1, 0, 100, NULL, '2025-11-30', 'Новый заказ'),
    (1, 2, 0, 50, NULL, '2025-11-25', 'Новый заказ');

-- Тестовые цены
INSERT OR IGNORE INTO component_prices (component_id, price, valid_from, notes) VALUES
    (1, 15.50, '2025-01-01', 'Цена с начала года'),
    (2, 18.00, '2025-01-01', 'Цена с начала года'),
    (3, 250.00, '2025-01-01', 'Цена с начала года'),
    (4, 5.00, '2025-01-01', 'Цена с начала года'),
    (5, 120.00, '2025-01-01', 'Цена с начала года');
