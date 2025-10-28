"""
ISO2 - Система управления документацией СМК
Точка входа в приложение
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import config
from gui_main import MainWindow


def select_work_folder():
    """Диалог выбора рабочей папки"""
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно

    messagebox.showinfo(
        "Первый запуск ISO2",
        "Добро пожаловать в ISO2!\n\n"
        "Выберите папку, где будут храниться документы.\n"
        "В этой папке будет создана структура:\n"
        "  • ПРОЕКТЫ\n"
        "  • ДЕЙСТВУЮЩИЕ\n"
        "  • АРХИВ\n"
        "  • РЕЕСТРЫ\n\n"
        "Рекомендуется создать новую папку 'ISO2_Docs'"
    )

    # Диалог выбора папки
    work_dir = filedialog.askdirectory(
        title="Выберите папку для хранения документов",
        mustexist=True
    )

    root.destroy()

    if not work_dir:
        # Пользователь отменил выбор
        messagebox.showerror("Ошибка", "Не выбрана рабочая папка.\nПриложение будет закрыто.")
        return None

    # Устанавливаем рабочую папку
    if not config.set_work_dir(work_dir):
        messagebox.showerror("Ошибка", "Не удалось сохранить настройки.\nПриложение будет закрыто.")
        return None

    messagebox.showinfo(
        "Настройка завершена",
        f"Рабочая папка установлена:\n{work_dir}\n\n"
        f"Структура папок создана успешно!"
    )

    return work_dir


def main():
    """Запуск приложения"""

    # Проверяем, установлена ли рабочая папка
    if not config.DOCS_DIR:
        # Первый запуск - выбираем папку
        if not select_work_folder():
            return

    # Запускаем главное окно
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()