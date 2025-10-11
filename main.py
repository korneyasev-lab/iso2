"""
ISO2 - Система управления документацией СМК
Точка входа в приложение
"""

import tkinter as tk
from gui_main import MainWindow


def main():
    """Запуск приложения"""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()