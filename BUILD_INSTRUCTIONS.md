# 🚀 Инструкция по компиляции ISO2

## Способ 1: PyInstaller (РЕКОМЕНДУЕТСЯ) ✅

PyInstaller работает надежно на macOS, Windows и Linux.

### Установка PyInstaller

```bash
pip install pyinstaller
```

### Компиляция

```bash
# Очистить старые сборки (опционально)
rm -rf build/ dist/

# Скомпилировать
pyinstaller ISO2.spec

# Готово! Приложение здесь:
# dist/ISO2.app
```

### Запуск

```bash
open dist/ISO2.app
```

Или перетащите `ISO2.app` в папку Applications.

---

## Способ 2: py2app (если PyInstaller не работает)

**⚠️ Внимание:** py2app может вызывать проблемы с подписью кода в Python 3.13

```bash
pip install py2app

# Очистить старые сборки
rm -rf build/ dist/

# Скомпилировать
python setup.py py2app

# Готово! Приложение здесь:
# dist/ISO2.app
```

---

## 📦 Структура после компиляции

```
iso2/
├── dist/
│   └── ISO2.app          ← Готовое приложение
├── build/                 ← Временные файлы (можно удалить)
├── main.py
├── config.py
├── gui_main.py
├── logic.py
└── ISO2.spec
```

---

## 🎯 Как использовать приложение

### Первый запуск

1. Запустите `ISO2.app`
2. Появится диалог "Первый запуск ISO2"
3. Выберите папку где хранить документы (например, `~/Documents/ISO2_Docs`)
4. Структура папок создастся автоматически

### Смена рабочей папки

- Нажмите кнопку **"⚙️ Сменить папку"** в главном окне
- Выберите новую папку

### Настройки хранятся

Настройки сохраняются в файле `iso2_settings.json` рядом с приложением.

---

## 🐛 Устранение проблем

### Ошибка "Cannot sign bundle" (py2app)

**Решение:** Используйте PyInstaller вместо py2app

```bash
pip install pyinstaller
pyinstaller ISO2.spec
```

### Приложение не запускается

**Проверьте:**
1. Python 3.8+ установлен
2. Все зависимости установлены: `pip install -r requirements.txt`
3. Права на запуск: `chmod +x dist/ISO2.app/Contents/MacOS/ISO2`

### macOS блокирует запуск

```bash
# Разрешить запуск неподписанного приложения
xattr -cr dist/ISO2.app
```

---

## 📝 Примечания

- **Первая компиляция** может занять 1-2 минуты
- **Размер приложения** ~50-100 MB (включает Python runtime)
- **Portable режим** - можно копировать на другие Mac без установки Python
