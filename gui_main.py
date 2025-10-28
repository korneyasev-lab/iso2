"""
GUI для ISO2
Главное окно с реестром документов и диалог публикации
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import subprocess
import platform
from datetime import datetime
from config import PROJECTS_DIR, ACTIVE_DIR, ARCHIVE_DIR, CATEGORIES, ACTIVE_CATEGORIES, ARCHIVE_CATEGORIES
from logic import (
    scan_folder, scan_folder_with_categories, find_similar_documents, compare_documents,
    publish_document, parse_filename, build_filename
)
from registry import (
    read_registry_content, export_registry_to_csv, export_registry_to_excel,
    export_all_registries_to_excel, manual_update_registry
)
from employees import (
    load_employees, add_employee, update_employee, delete_employee,
    export_employees_to_excel, create_familiarization_sheet
)


class MainWindow:
    """Главное окно приложения"""

    def __init__(self, root):
        self.root = root
        self.root.title("ISO2 - Управление документацией СМК")
        self.root.geometry("1200x700")
        self.root.configure(bg="#2C3E50")

        # Текущие документы
        self.current_folder = PROJECTS_DIR
        self.documents = []
        self.current_category = None  # Текущая выбранная категория (для фильтра)

        # Настройка стилей
        self.setup_styles()

        self.create_widgets()
        self.load_documents()

    def setup_styles(self):
        """Настройка стилей ttk"""
        style = ttk.Style()
        style.theme_use('default')

        # Стиль для кнопок
        style.configure("TButton",
                        font=("Arial", 14, "bold"),
                        foreground="white",
                        background="#4A5568",
                        borderwidth=2,
                        relief=tk.RAISED,
                        padding=5)
        style.map("TButton",
                  background=[('active', '#5A6678'), ('pressed', '#3A4558')],
                  foreground=[('active', 'white')])

        # Стиль для кнопки публикации (чуть светлее)
        style.configure("Publish.TButton",
                        font=("Arial", 14, "bold"),
                        foreground="white",
                        background="#546E7A",
                        borderwidth=2,
                        relief=tk.RAISED,
                        padding=5)
        style.map("Publish.TButton",
                  background=[('active', '#607D8B'), ('pressed', '#446E7A')],
                  foreground=[('active', 'white')])

        # Стиль для Treeview
        style.configure("Treeview",
                        background="#37474F",
                        foreground="white",
                        fieldbackground="#37474F",
                        font=("Arial", 14),
                        rowheight=35)
        style.configure("Treeview.Heading",
                        background="#2C3E50",
                        foreground="white",
                        font=("Arial", 14, "bold"),
                        relief=tk.FLAT)
        style.map("Treeview",
                  background=[('selected', '#546E7A')],
                  foreground=[('selected', 'white')])

        # Стиль для Combobox
        style.configure("TCombobox",
                        font=("Arial", 14),
                        foreground="black",
                        background="white",
                        fieldbackground="white",
                        selectbackground="#546E7A",
                        selectforeground="white")

    def create_widgets(self):
        """Создание элементов интерфейса"""

        # Верхняя панель с кнопками
        top_frame = tk.Frame(self.root, bg="#37474F")
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Кнопки выбора папки
        ttk.Button(
            top_frame, text="ПРОЕКТЫ", width=15,
            command=lambda: self.switch_folder(PROJECTS_DIR),
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            top_frame, text="ДЕЙСТВУЮЩИЕ", width=15,
            command=lambda: self.switch_folder(ACTIVE_DIR),
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            top_frame, text="АРХИВ", width=15,
            command=lambda: self.switch_folder(ARCHIVE_DIR),
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        # Кнопка реестров
        ttk.Button(
            top_frame, text="РЕЕСТРЫ", width=15,
            command=self.open_registry_window,
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        # Кнопка сотрудников
        ttk.Button(
            top_frame, text="СОТРУДНИКИ", width=15,
            command=self.open_employees_window,
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        # Разделитель
        tk.Frame(top_frame, width=30, bg="#37474F").pack(side=tk.LEFT)

        # Кнопка публикации
        self.publish_btn = ttk.Button(
            top_frame, text="📤 Опубликовать", width=20,
            command=self.open_publish_dialog,
            style="Publish.TButton"
        )
        self.publish_btn.pack(side=tk.LEFT, padx=5)

        # Кнопка листа ознакомления
        self.familiarization_btn = ttk.Button(
            top_frame, text="📄 Лист ознакомления", width=22,
            command=self.open_familiarization_dialog,
            style="Publish.TButton"
        )
        self.familiarization_btn.pack(side=tk.LEFT, padx=5)

        # Разделитель
        tk.Frame(top_frame, width=30, bg="#37474F").pack(side=tk.LEFT)

        # Кнопка смены рабочей папки
        ttk.Button(
            top_frame, text="⚙️ Сменить папку", width=18,
            command=self.change_work_folder,
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        # Метка текущей папки и фильтр категорий
        folder_filter_frame = tk.Frame(self.root, bg="#455A64", height=60)
        folder_filter_frame.pack(fill=tk.X, padx=10)
        folder_filter_frame.pack_propagate(False)

        # Левая часть - название папки
        self.folder_label = tk.Label(
            folder_filter_frame, text="", font=("Arial", 16, "bold"),
            bg="#455A64", fg="white", anchor="w", padx=10
        )
        self.folder_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Правая часть - фильтр по категориям
        filter_frame = tk.Frame(folder_filter_frame, bg="#455A64")
        filter_frame.pack(side=tk.RIGHT, padx=10)

        self.category_label = tk.Label(
            filter_frame, text="Категория:", font=("Arial", 14, "bold"),
            bg="#455A64", fg="white"
        )

        self.category_combo = ttk.Combobox(
            filter_frame,
            values=["Все категории"] + CATEGORIES,
            state="readonly",
            font=("Arial", 14),
            width=20
        )
        self.category_combo.current(0)
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_change)

        # Таблица документов
        table_frame = tk.Frame(self.root, bg="#2C3E50")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbar
        scrollbar = tk.Scrollbar(table_frame, bg="#37474F")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview - ОДНА колонка "Название документа"
        columns = ("Название документа",)
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)

        # Настройка колонки
        self.tree.heading("Название документа", text="Название документа")
        self.tree.column("Название документа", width=1100)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Двойной клик - открыть файл
        self.tree.bind('<Double-1>', self.open_document)

        # Клик - выбор документа (для активации кнопок)
        self.tree.bind('<<TreeviewSelect>>', self.on_document_select)

        # Статус бар
        self.status_label = tk.Label(
            self.root, text="Готов", anchor="w",
            bg="#37474F", fg="white", relief=tk.SUNKEN,
            font=("Arial", 14), height=2
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def switch_folder(self, folder_path):
        """Переключение между папками"""
        self.current_folder = folder_path
        self.current_category = None
        self.category_combo.current(0)  # Сбрасываем фильтр на "Все категории"

        # Показываем/скрываем фильтр категорий
        if folder_path in [ACTIVE_DIR, ARCHIVE_DIR]:
            self.category_label.pack(side=tk.LEFT, padx=5)
            self.category_combo.pack(side=tk.LEFT, padx=5)
        else:
            self.category_label.pack_forget()
            self.category_combo.pack_forget()

        self.load_documents()

        # Активируем кнопку публикации только для ПРОЕКТОВ
        if folder_path == PROJECTS_DIR:
            self.publish_btn.config(state=tk.NORMAL)
        else:
            self.publish_btn.config(state=tk.DISABLED)

        # Активируем кнопку листа ознакомления только для ДЕЙСТВУЮЩИХ
        if folder_path == ACTIVE_DIR:
            self.familiarization_btn.config(state=tk.DISABLED)  # Будет активна при выборе документа
        else:
            self.familiarization_btn.config(state=tk.DISABLED)

    def on_category_change(self, event=None):
        """Обработка изменения фильтра категорий"""
        selected = self.category_combo.get()

        if selected == "Все категории":
            self.current_category = None
        else:
            self.current_category = selected

        self.filter_documents()

    def load_documents(self):
        """Загрузка документов из текущей папки"""
        if self.current_folder == PROJECTS_DIR:
            # В ПРОЕКТАХ - обычное сканирование без категорий
            self.documents = scan_folder(self.current_folder)
        elif self.current_folder == ACTIVE_DIR:
            # В ДЕЙСТВУЮЩИХ - сканирование с категориями
            self.documents = scan_folder_with_categories(ACTIVE_DIR, ACTIVE_CATEGORIES)
        elif self.current_folder == ARCHIVE_DIR:
            # В АРХИВЕ - сканирование с категориями
            self.documents = scan_folder_with_categories(ARCHIVE_DIR, ARCHIVE_CATEGORIES)
        else:
            self.documents = []

        # Обновляем метку папки
        folder_name = os.path.basename(self.current_folder)
        self.folder_label.config(text=f"📁 {folder_name} ({len(self.documents)} документов)")

        # Обновляем таблицу
        self.filter_documents()

    def filter_documents(self):
        """Отображение документов с учетом фильтра категорий"""
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Фильтруем документы по категории
        if self.current_category:
            filtered_docs = [doc for doc in self.documents if doc.category == self.current_category]
        else:
            filtered_docs = self.documents

        # Добавляем документы в таблицу
        for doc in filtered_docs:
            # Определяем что показывать
            if self.current_folder == PROJECTS_DIR:
                # В ПРОЕКТАХ - имя файла КАК ЕСТЬ
                display_name = doc.filename
            else:
                # В ДЕЙСТВУЮЩИХ/АРХИВ - собранное имя (парсинг + слияние) + категория
                if doc.is_valid:
                    display_name = build_filename(doc.typ, doc.kod, doc.version, doc.year, doc.title)
                    if doc.category:
                        display_name = f"[{doc.category}] {display_name}"
                else:
                    display_name = doc.filename
                    if doc.category:
                        display_name = f"[{doc.category}] {display_name}"

            self.tree.insert("", tk.END, values=(display_name,), tags=(doc.filename, doc.category if doc.category else ""))

        # Обновляем статус
        self.status_label.config(text=f"Показано документов: {len(filtered_docs)}")

    def open_document(self, event):
        """Открыть документ (двойной клик)"""
        selection = self.tree.selection()
        if not selection:
            return

        # Получаем filename и category из tags
        tags = self.tree.item(selection[0])['tags']
        if not tags:
            return

        filename = tags[0]
        category = tags[1] if len(tags) > 1 and tags[1] else None

        # Находим документ
        doc = next((d for d in self.documents if d.filename == filename and d.category == category), None)
        if doc:
            # Открываем файл кроссплатформенно
            try:
                if platform.system() == 'Darwin':  # macOS
                    subprocess.call(['open', doc.full_path])
                elif platform.system() == 'Windows':
                    os.startfile(doc.full_path)
                else:  # Linux
                    subprocess.call(['xdg-open', doc.full_path])
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")

    def on_document_select(self, event=None):
        """Обработка выбора документа в таблице"""
        selection = self.tree.selection()

        # Активируем кнопку листа ознакомления только если выбран документ и открыта папка ДЕЙСТВУЮЩИЕ
        if selection and self.current_folder == ACTIVE_DIR:
            self.familiarization_btn.config(state=tk.NORMAL)
        else:
            if self.current_folder == ACTIVE_DIR:
                self.familiarization_btn.config(state=tk.DISABLED)

    def open_publish_dialog(self):
        """Открыть диалог публикации"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите документ для публикации")
            return

        # Получаем filename из tags
        tags = self.tree.item(selection[0])['tags']
        if not tags:
            return

        filename = tags[0]

        # Находим документ
        doc = next((d for d in self.documents if d.filename == filename), None)
        if doc:
            dialog = PublishDialog(self.root, doc, self)
            self.root.wait_window(dialog.dialog)

    def open_familiarization_dialog(self):
        """Открыть диалог создания листа ознакомления"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите документ из ДЕЙСТВУЮЩИХ")
            return

        # Получаем filename и category из tags
        tags = self.tree.item(selection[0])['tags']
        if not tags:
            return

        filename = tags[0]
        category = tags[1] if len(tags) > 1 and tags[1] else None

        # Находим документ
        doc = next((d for d in self.documents if d.filename == filename and d.category == category), None)
        if doc:
            dialog = FamiliarizationDialog(self.root, doc)
            self.root.wait_window(dialog.dialog)

    def open_registry_window(self):
        """Открыть окно просмотра реестров"""
        registry_window = RegistryWindow(self.root)
        self.root.wait_window(registry_window.window)

    def open_employees_window(self):
        """Открыть окно управления сотрудниками"""
        employees_window = EmployeesWindow(self.root)
        self.root.wait_window(employees_window.window)

    def change_work_folder(self):
        """Сменить рабочую папку"""
        import config

        # Показываем текущую папку
        current = config.DOCS_DIR if config.DOCS_DIR else "не установлена"

        result = messagebox.askyesno(
            "Смена рабочей папки",
            f"Текущая рабочая папка:\n{current}\n\n"
            f"Вы хотите выбрать другую папку для хранения документов?"
        )

        if not result:
            return

        # Диалог выбора новой папки
        new_dir = filedialog.askdirectory(
            title="Выберите новую папку для хранения документов",
            mustexist=True
        )

        if not new_dir:
            return

        # Устанавливаем новую папку
        if config.set_work_dir(new_dir):
            messagebox.showinfo(
                "Успех",
                f"Рабочая папка изменена на:\n{new_dir}\n\n"
                f"Приложение будет перезапущено."
            )

            # Перезапускаем окно
            self.root.destroy()

            # Создаём новое окно
            import tkinter as tk
            new_root = tk.Tk()
            from gui_main import MainWindow
            MainWindow(new_root)
            new_root.mainloop()
        else:
            messagebox.showerror(
                "Ошибка",
                "Не удалось изменить рабочую папку"
            )


class PublishDialog:
    """Диалоговое окно публикации документа"""

    def __init__(self, parent, document, main_window):
        self.document = document
        self.main_window = main_window

        # Создаём диалоговое окно
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Публикация документа")
        self.dialog.geometry("900x650")
        self.dialog.configure(bg="#2C3E50")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Список похожих документов с галочками
        self.similar_docs = []
        self.archive_vars = {}  # {doc: BooleanVar}

        self.create_widgets()
        self.find_similar()

    def create_widgets(self):
        """Создание элементов диалога"""

        # Заголовок
        tk.Label(
            self.dialog, text="Публикация документа",
            font=("Arial", 16, "bold"), bg="#37474F", fg="white", pady=10
        ).pack(fill=tk.X)

        # Исходный файл
        frame1 = tk.LabelFrame(self.dialog, text="Файл из ПРОЕКТОВ",
                               padx=10, pady=10, font=("Arial", 14, "bold"),
                               bg="#37474F", fg="white")
        frame1.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame1, text=self.document.filename,
                 font=("Arial", 14), bg="#37474F", fg="white").pack(anchor="w")

        # Поля для редактирования
        frame2 = tk.LabelFrame(self.dialog, text="Редактировать данные документа",
                               padx=10, pady=10, font=("Arial", 14, "bold"),
                               bg="#37474F", fg="white")
        frame2.pack(fill=tk.X, padx=10, pady=5)

        # Тип
        row1 = tk.Frame(frame2, bg="#37474F")
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="Тип:", width=10, anchor="w",
                 font=("Arial", 14), bg="#37474F", fg="white").pack(side=tk.LEFT)
        self.typ_var = tk.StringVar(value=self.document.typ)
        tk.Entry(row1, textvariable=self.typ_var, width=20,
                 font=("Arial", 14), bg="#4A5568", fg="white",
                 insertbackground="white").pack(side=tk.LEFT)

        # Код
        row2 = tk.Frame(frame2, bg="#37474F")
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="Код:", width=10, anchor="w",
                 font=("Arial", 14), bg="#37474F", fg="white").pack(side=tk.LEFT)
        self.kod_var = tk.StringVar(value=self.document.kod)
        tk.Entry(row2, textvariable=self.kod_var, width=20,
                 font=("Arial", 14), bg="#4A5568", fg="white",
                 insertbackground="white").pack(side=tk.LEFT)

        # Версия
        row3 = tk.Frame(frame2, bg="#37474F")
        row3.pack(fill=tk.X, pady=2)
        tk.Label(row3, text="Версия:", width=10, anchor="w",
                 font=("Arial", 14), bg="#37474F", fg="white").pack(side=tk.LEFT)
        self.version_var = tk.StringVar(value=self.document.version)
        tk.Entry(row3, textvariable=self.version_var, width=20,
                 font=("Arial", 14), bg="#4A5568", fg="white",
                 insertbackground="white").pack(side=tk.LEFT)

        # Год
        row4 = tk.Frame(frame2, bg="#37474F")
        row4.pack(fill=tk.X, pady=2)
        tk.Label(row4, text="Год:", width=10, anchor="w",
                 font=("Arial", 14), bg="#37474F", fg="white").pack(side=tk.LEFT)
        self.year_var = tk.StringVar(value=self.document.year)
        tk.Entry(row4, textvariable=self.year_var, width=20,
                 font=("Arial", 14), bg="#4A5568", fg="white",
                 insertbackground="white").pack(side=tk.LEFT)

        # Название
        row5 = tk.Frame(frame2, bg="#37474F")
        row5.pack(fill=tk.X, pady=2)
        tk.Label(row5, text="Название:", width=10, anchor="w",
                 font=("Arial", 14), bg="#37474F", fg="white").pack(side=tk.LEFT)
        self.title_var = tk.StringVar(value=self.document.title)
        tk.Entry(row5, textvariable=self.title_var, width=50,
                 font=("Arial", 14), bg="#4A5568", fg="white",
                 insertbackground="white").pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Категория
        row6 = tk.Frame(frame2, bg="#37474F")
        row6.pack(fill=tk.X, pady=2)
        tk.Label(row6, text="Категория:", width=10, anchor="w",
                 font=("Arial", 14), bg="#37474F", fg="white").pack(side=tk.LEFT)

        self.category_var = tk.StringVar(value=CATEGORIES[0])
        category_combo = ttk.Combobox(
            row6,
            textvariable=self.category_var,
            values=CATEGORIES,
            state="readonly",
            font=("Arial", 14),
            width=25
        )
        category_combo.pack(side=tk.LEFT)

        # Обновление предпросмотра при изменении полей
        for var in [self.typ_var, self.kod_var, self.version_var, self.year_var, self.title_var]:
            var.trace('w', lambda *args: self.update_preview())

        # Похожие документы
        self.similar_frame = tk.LabelFrame(
            self.dialog, text="Похожие документы в ДЕЙСТВУЮЩИХ",
            padx=10, pady=10, font=("Arial", 14, "bold"),
            bg="#37474F", fg="white", height=200
        )
        self.similar_frame.pack(fill=tk.BOTH, padx=10, pady=5)
        self.similar_frame.pack_propagate(False)  # Фиксируем высоту

        # Scrollable frame для похожих документов
        canvas = tk.Canvas(self.similar_frame, bg="#37474F", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.similar_frame, orient="vertical", command=canvas.yview, bg="#4A5568")
        self.scrollable_frame = tk.Frame(canvas, bg="#37474F")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Предпросмотр нового имени
        frame4 = tk.LabelFrame(self.dialog, text="Новое имя файла (предпросмотр)",
                               padx=10, pady=10, font=("Arial", 14, "bold"),
                               bg="#37474F", fg="white")
        frame4.pack(fill=tk.X, padx=10, pady=5)

        self.preview_label = tk.Label(
            frame4, text="", font=("Arial", 14, "bold"),
            fg="#90CAF9", bg="#37474F", anchor="w"
        )
        self.preview_label.pack(fill=tk.X)

        # Кнопки
        button_frame = tk.Frame(self.dialog, bg="#2C3E50")
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame, text="Отмена", width=15,
            command=self.dialog.destroy,
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, text="Опубликовать", width=15,
            command=self.publish,
            style="Publish.TButton"
        ).pack(side=tk.LEFT, padx=5)

        # Обновляем предпросмотр
        self.update_preview()

    def find_similar(self):
        """Поиск и отображение похожих документов"""
        # Загружаем действующие документы из всех категорий
        active_docs = scan_folder_with_categories(ACTIVE_DIR, ACTIVE_CATEGORIES)

        # Ищем похожие
        self.similar_docs = find_similar_documents(self.document, active_docs)

        # Очищаем фрейм
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not self.similar_docs:
            tk.Label(
                self.scrollable_frame, text="Похожих документов не найдено",
                fg="#B0BEC5", font=("Arial", 14, "italic"), bg="#37474F"
            ).pack(pady=20)
            return

        # Отображаем похожие документы
        for doc in self.similar_docs:
            frame = tk.Frame(self.scrollable_frame, relief=tk.RIDGE,
                             borderwidth=2, padx=10, pady=10, bg="#4A5568")
            frame.pack(fill=tk.X, pady=5)

            # Галочка
            var = tk.BooleanVar(value=True)  # По умолчанию включена
            self.archive_vars[doc] = var

            chk = tk.Checkbutton(
                frame, variable=var, text="",
                font=("Arial", 14), bg="#4A5568", fg="white",
                selectcolor="#37474F", activebackground="#4A5568"
            )
            chk.pack(side=tk.LEFT)

            # Информация о документе
            info_frame = tk.Frame(frame, bg="#4A5568")
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Собранное имя документа с категорией
            if doc.is_valid:
                doc_display = build_filename(doc.typ, doc.kod, doc.version, doc.year, doc.title)
            else:
                doc_display = doc.filename

            if doc.category:
                doc_display = f"[{doc.category}] {doc_display}"

            tk.Label(
                info_frame, text=doc_display,
                font=("Arial", 14, "bold"), bg="#4A5568", fg="white"
            ).pack(anchor="w")

            # Сравнение
            comparison = compare_documents(self.document, doc)

            if comparison['matches']:
                matches_text = "Совпадения: " + " ".join(comparison['matches'])
                tk.Label(
                    info_frame, text=matches_text,
                    fg="#81C784", font=("Arial", 12), bg="#4A5568"
                ).pack(anchor="w")

            if comparison['differences']:
                diff_text = "Различия: " + " ".join(comparison['differences'])
                tk.Label(
                    info_frame, text=diff_text,
                    fg="#FFB74D", font=("Arial", 12), bg="#4A5568"
                ).pack(anchor="w")

    def update_preview(self):
        """Обновить предпросмотр нового имени"""
        typ = self.typ_var.get()
        kod = self.kod_var.get()
        version = self.version_var.get()
        year = self.year_var.get()
        title = self.title_var.get()

        if all([typ, kod, version, year, title]):
            ext = os.path.splitext(self.document.filename)[1]
            new_name = build_filename(typ, kod, version, year, title) + ext
            self.preview_label.config(text=new_name)
        else:
            self.preview_label.config(text="(заполните все поля)")

    def publish(self):
        """Выполнить публикацию"""
        # Получаем данные
        typ = self.typ_var.get().strip()
        kod = self.kod_var.get().strip()
        version = self.version_var.get().strip()
        year = self.year_var.get().strip()
        title = self.title_var.get().strip()
        category = self.category_var.get()

        # Проверка заполненности
        if not all([typ, kod, version, year, title, category]):
            messagebox.showerror("Ошибка", "Заполните все поля, включая категорию")
            return

        # Список документов для архивации
        archive_list = [doc for doc, var in self.archive_vars.items() if var.get()]

        # Подтверждение
        msg = f"Опубликовать документ?\n\n"
        msg += f"Новое имя: {build_filename(typ, kod, version, year, title)}\n"
        msg += f"Категория: {category}\n\n"
        if archive_list:
            msg += f"В архив будет перемещено документов: {len(archive_list)}"

        if not messagebox.askyesno("Подтверждение", msg):
            return

        # Публикация
        success = publish_document(
            self.document, typ, kod, version, year, title, category, archive_list
        )

        if success:
            messagebox.showinfo("Успех", "Документ успешно опубликован!")
            self.main_window.load_documents()  # Обновляем главное окно
            self.dialog.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось опубликовать документ")


class RegistryWindow:
    """Окно просмотра и экспорта реестров"""

    def __init__(self, parent):
        # Создаём окно
        self.window = tk.Toplevel(parent)
        self.window.title("Реестры документации СМК")
        self.window.geometry("1000x700")
        self.window.configure(bg="#2C3E50")
        self.window.transient(parent)
        self.window.grab_set()

        self.current_category = CATEGORIES[0]  # Текущая выбранная категория

        self.create_widgets()
        self.load_registry()

    def create_widgets(self):
        """Создание элементов интерфейса"""

        # Заголовок
        header = tk.Label(
            self.window, text="📋 Реестры действующих документов",
            font=("Arial", 18, "bold"), bg="#37474F", fg="white", pady=15
        )
        header.pack(fill=tk.X)

        # Панель выбора категории и кнопок
        control_frame = tk.Frame(self.window, bg="#455A64", pady=10)
        control_frame.pack(fill=tk.X, padx=10)

        # Выбор категории
        tk.Label(
            control_frame, text="Категория:", font=("Arial", 14, "bold"),
            bg="#455A64", fg="white"
        ).pack(side=tk.LEFT, padx=10)

        self.category_var = tk.StringVar(value=self.current_category)
        self.category_combo = ttk.Combobox(
            control_frame,
            textvariable=self.category_var,
            values=CATEGORIES,
            state="readonly",
            font=("Arial", 14),
            width=25
        )
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_change)

        # Разделитель
        tk.Frame(control_frame, width=30, bg="#455A64").pack(side=tk.LEFT)

        # Кнопка обновления реестра
        ttk.Button(
            control_frame, text="🔄 Обновить реестр", width=20,
            command=self.update_registry,
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        # Панель кнопок экспорта
        export_frame = tk.Frame(self.window, bg="#455A64", pady=10)
        export_frame.pack(fill=tk.X, padx=10)

        tk.Label(
            export_frame, text="Экспорт:", font=("Arial", 14, "bold"),
            bg="#455A64", fg="white"
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            export_frame, text="💾 CSV (текущая категория)", width=25,
            command=self.export_csv,
            style="Publish.TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            export_frame, text="📊 Excel (текущая категория)", width=28,
            command=self.export_excel_single,
            style="Publish.TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            export_frame, text="📚 Excel (все категории)", width=25,
            command=self.export_excel_all,
            style="Publish.TButton"
        ).pack(side=tk.LEFT, padx=5)

        # Текстовое поле для отображения реестра
        text_frame = tk.Frame(self.window, bg="#2C3E50")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame, bg="#37474F")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Text widget
        self.text_widget = tk.Text(
            text_frame,
            font=("Courier New", 12),
            bg="#37474F",
            fg="white",
            insertbackground="white",
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_widget.yview)

        # Статус бар
        self.status_label = tk.Label(
            self.window, text="Готов", anchor="w",
            bg="#37474F", fg="white", relief=tk.SUNKEN,
            font=("Arial", 12), height=2
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Кнопка закрытия
        close_frame = tk.Frame(self.window, bg="#2C3E50")
        close_frame.pack(pady=10)

        ttk.Button(
            close_frame, text="Закрыть", width=15,
            command=self.window.destroy,
            style="TButton"
        ).pack()

    def on_category_change(self, event=None):
        """Обработка изменения категории"""
        self.current_category = self.category_var.get()
        self.load_registry()

    def load_registry(self):
        """Загрузить и отобразить реестр для текущей категории"""
        self.text_widget.delete(1.0, tk.END)

        content = read_registry_content(self.current_category)
        self.text_widget.insert(1.0, content)

        self.status_label.config(text=f"Загружен реестр: {self.current_category}")

    def update_registry(self):
        """Принудительное обновление реестра"""
        success = manual_update_registry(self.current_category)

        if success:
            messagebox.showinfo("Успех", f"Реестр для категории '{self.current_category}' обновлён!")
            self.load_registry()
        else:
            messagebox.showerror("Ошибка", "Не удалось обновить реестр")

    def export_csv(self):
        """Экспорт текущего реестра в CSV"""
        # Диалог сохранения файла
        default_name = f"Реестр_{self.current_category.replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d')}.csv"
        filepath = filedialog.asksaveasfilename(
            title="Сохранить реестр как CSV",
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
            initialfile=default_name
        )

        if not filepath:
            return

        success = export_registry_to_csv(self.current_category, filepath)

        if success:
            messagebox.showinfo("Успех", f"Реестр экспортирован в:\n{filepath}")
            self.status_label.config(text=f"Экспортировано в CSV: {os.path.basename(filepath)}")
        else:
            messagebox.showerror("Ошибка", "Не удалось экспортировать реестр")

    def export_excel_single(self):
        """Экспорт текущего реестра в Excel"""
        # Диалог сохранения файла
        default_name = f"Реестр_{self.current_category.replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        filepath = filedialog.asksaveasfilename(
            title="Сохранить реестр как Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel файлы", "*.xlsx"), ("Все файлы", "*.*")],
            initialfile=default_name
        )

        if not filepath:
            return

        success = export_registry_to_excel(self.current_category, filepath)

        if success:
            messagebox.showinfo("Успех", f"Реестр экспортирован в:\n{filepath}")
            self.status_label.config(text=f"Экспортировано в Excel: {os.path.basename(filepath)}")
        else:
            messagebox.showerror("Ошибка", "Не удалось экспортировать реестр.\nУбедитесь что установлена библиотека openpyxl:\npip install openpyxl")

    def export_excel_all(self):
        """Экспорт всех реестров в один Excel файл"""
        # Диалог сохранения файла
        default_name = f"Реестры_СМК_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        filepath = filedialog.asksaveasfilename(
            title="Сохранить все реестры как Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel файлы", "*.xlsx"), ("Все файлы", "*.*")],
            initialfile=default_name
        )

        if not filepath:
            return

        success = export_all_registries_to_excel(filepath)

        if success:
            messagebox.showinfo("Успех", f"Все реестры экспортированы в:\n{filepath}")
            self.status_label.config(text=f"Экспортированы все реестры в Excel: {os.path.basename(filepath)}")
        else:
            messagebox.showerror("Ошибка", "Не удалось экспортировать реестры.\nУбедитесь что установлена библиотека openpyxl:\npip install openpyxl")


class EmployeesWindow:
    """Окно управления справочником сотрудников"""

    def __init__(self, parent):
        # Создаём окно
        self.window = tk.Toplevel(parent)
        self.window.title("Справочник сотрудников")
        self.window.geometry("1000x600")
        self.window.configure(bg="#2C3E50")
        self.window.transient(parent)
        self.window.grab_set()

        self.employees = []  # Список сотрудников
        self.selected_employee = None  # Выбранный сотрудник

        self.create_widgets()
        self.load_employees_list()

    def create_widgets(self):
        """Создание элементов интерфейса"""

        # Заголовок
        header = tk.Label(
            self.window, text="👥 Справочник сотрудников",
            font=("Arial", 18, "bold"), bg="#37474F", fg="white", pady=15
        )
        header.pack(fill=tk.X)

        # Панель кнопок управления
        control_frame = tk.Frame(self.window, bg="#455A64", pady=10)
        control_frame.pack(fill=tk.X, padx=10)

        ttk.Button(
            control_frame, text="➕ Добавить", width=15,
            command=self.add_employee_dialog,
            style="Publish.TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame, text="✏️ Редактировать", width=18,
            command=self.edit_employee_dialog,
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame, text="🗑️ Удалить", width=15,
            command=self.delete_employee_action,
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        # Разделитель
        tk.Frame(control_frame, width=30, bg="#455A64").pack(side=tk.LEFT)

        ttk.Button(
            control_frame, text="📊 Экспорт в Excel", width=18,
            command=self.export_to_excel,
            style="Publish.TButton"
        ).pack(side=tk.LEFT, padx=5)

        # Таблица сотрудников
        table_frame = tk.Frame(self.window, bg="#2C3E50")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbar
        scrollbar = tk.Scrollbar(table_frame, bg="#37474F")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview
        columns = ("ФИО", "Должность", "Подразделение", "Email")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)

        # Настройка колонок
        self.tree.heading("ФИО", text="ФИО")
        self.tree.heading("Должность", text="Должность")
        self.tree.heading("Подразделение", text="Подразделение")
        self.tree.heading("Email", text="Email")

        self.tree.column("ФИО", width=300)
        self.tree.column("Должность", width=250)
        self.tree.column("Подразделение", width=120)
        self.tree.column("Email", width=250)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Обработка выбора строки
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # Статус бар
        self.status_label = tk.Label(
            self.window, text="Готов", anchor="w",
            bg="#37474F", fg="white", relief=tk.SUNKEN,
            font=("Arial", 12), height=2
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Кнопка закрытия
        close_frame = tk.Frame(self.window, bg="#2C3E50")
        close_frame.pack(pady=10)

        ttk.Button(
            close_frame, text="Закрыть", width=15,
            command=self.window.destroy,
            style="TButton"
        ).pack()

    def load_employees_list(self):
        """Загрузить и отобразить список сотрудников"""
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Загружаем сотрудников
        self.employees = load_employees()

        # Добавляем в таблицу
        for emp in self.employees:
            self.tree.insert("", tk.END, values=(
                emp['fio'],
                emp['position'],
                emp['department'],
                emp['email']
            ), tags=(emp['id'],))

        self.status_label.config(text=f"Загружено сотрудников: {len(self.employees)}")

    def on_select(self, event):
        """Обработка выбора строки"""
        selection = self.tree.selection()
        if selection:
            tags = self.tree.item(selection[0])['tags']
            if tags:
                emp_id = tags[0]
                self.selected_employee = next((emp for emp in self.employees if emp['id'] == emp_id), None)

    def add_employee_dialog(self):
        """Диалог добавления сотрудника"""
        dialog = EmployeeEditDialog(self.window, None, self)
        self.window.wait_window(dialog.dialog)

    def edit_employee_dialog(self):
        """Диалог редактирования сотрудника"""
        if not self.selected_employee:
            messagebox.showwarning("Предупреждение", "Выберите сотрудника для редактирования")
            return

        dialog = EmployeeEditDialog(self.window, self.selected_employee, self)
        self.window.wait_window(dialog.dialog)

    def delete_employee_action(self):
        """Удалить выбранного сотрудника"""
        if not self.selected_employee:
            messagebox.showwarning("Предупреждение", "Выберите сотрудника для удаления")
            return

        # Подтверждение
        if not messagebox.askyesno("Подтверждение",
                                    f"Удалить сотрудника:\n{self.selected_employee['fio']}?"):
            return

        success = delete_employee(self.selected_employee['id'])

        if success:
            messagebox.showinfo("Успех", "Сотрудник удалён")
            self.load_employees_list()
            self.selected_employee = None
        else:
            messagebox.showerror("Ошибка", "Не удалось удалить сотрудника")

    def export_to_excel(self):
        """Экспорт списка сотрудников в Excel"""
        if not self.employees:
            messagebox.showwarning("Предупреждение", "Список сотрудников пуст")
            return

        # Диалог сохранения файла
        default_name = f"Сотрудники_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        filepath = filedialog.asksaveasfilename(
            title="Сохранить список сотрудников",
            defaultextension=".xlsx",
            filetypes=[("Excel файлы", "*.xlsx"), ("Все файлы", "*.*")],
            initialfile=default_name
        )

        if not filepath:
            return

        success = export_employees_to_excel(filepath)

        if success:
            messagebox.showinfo("Успех", f"Список сотрудников экспортирован в:\n{filepath}")
            self.status_label.config(text=f"Экспортировано в Excel: {os.path.basename(filepath)}")
        else:
            messagebox.showerror("Ошибка",
                                 "Не удалось экспортировать список.\nУбедитесь что установлена библиотека openpyxl:\npip install openpyxl")


class EmployeeEditDialog:
    """Диалог добавления/редактирования сотрудника"""

    def __init__(self, parent, employee, employees_window):
        self.employee = employee  # None для добавления, объект для редактирования
        self.employees_window = employees_window

        # Создаём диалоговое окно
        self.dialog = tk.Toplevel(parent)
        title = "Редактирование сотрудника" if employee else "Добавление сотрудника"
        self.dialog.title(title)
        self.dialog.geometry("600x400")
        self.dialog.configure(bg="#2C3E50")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.create_widgets()

    def create_widgets(self):
        """Создание элементов диалога"""

        # Заголовок
        header_text = "✏️ Редактирование" if self.employee else "➕ Добавление"
        tk.Label(
            self.dialog, text=header_text,
            font=("Arial", 16, "bold"), bg="#37474F", fg="white", pady=10
        ).pack(fill=tk.X)

        # Форма
        form_frame = tk.LabelFrame(
            self.dialog, text="Данные сотрудника",
            padx=20, pady=20, font=("Arial", 14, "bold"),
            bg="#37474F", fg="white"
        )
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # ФИО
        row1 = tk.Frame(form_frame, bg="#37474F")
        row1.pack(fill=tk.X, pady=5)
        tk.Label(row1, text="ФИО:", width=15, anchor="w",
                 font=("Arial", 12), bg="#37474F", fg="white").pack(side=tk.LEFT)
        self.fio_var = tk.StringVar(value=self.employee['fio'] if self.employee else "")
        tk.Entry(row1, textvariable=self.fio_var, width=40,
                 font=("Arial", 12), bg="#4A5568", fg="white",
                 insertbackground="white").pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Должность
        row2 = tk.Frame(form_frame, bg="#37474F")
        row2.pack(fill=tk.X, pady=5)
        tk.Label(row2, text="Должность:", width=15, anchor="w",
                 font=("Arial", 12), bg="#37474F", fg="white").pack(side=tk.LEFT)
        self.position_var = tk.StringVar(value=self.employee['position'] if self.employee else "")
        tk.Entry(row2, textvariable=self.position_var, width=40,
                 font=("Arial", 12), bg="#4A5568", fg="white",
                 insertbackground="white").pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Подразделение
        row3 = tk.Frame(form_frame, bg="#37474F")
        row3.pack(fill=tk.X, pady=5)
        tk.Label(row3, text="Подразделение:", width=15, anchor="w",
                 font=("Arial", 12), bg="#37474F", fg="white").pack(side=tk.LEFT)
        self.department_var = tk.StringVar(value=self.employee['department'] if self.employee else "ФБП")
        department_combo = ttk.Combobox(
            row3,
            textvariable=self.department_var,
            values=["ФБП", "НПФ"],
            state="readonly",
            font=("Arial", 12),
            width=20
        )
        department_combo.pack(side=tk.LEFT)

        # Email
        row4 = tk.Frame(form_frame, bg="#37474F")
        row4.pack(fill=tk.X, pady=5)
        tk.Label(row4, text="Email:", width=15, anchor="w",
                 font=("Arial", 12), bg="#37474F", fg="white").pack(side=tk.LEFT)
        self.email_var = tk.StringVar(value=self.employee['email'] if self.employee else "")
        tk.Entry(row4, textvariable=self.email_var, width=40,
                 font=("Arial", 12), bg="#4A5568", fg="white",
                 insertbackground="white").pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Кнопки
        button_frame = tk.Frame(self.dialog, bg="#2C3E50")
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame, text="Отмена", width=15,
            command=self.dialog.destroy,
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        save_text = "Сохранить" if self.employee else "Добавить"
        ttk.Button(
            button_frame, text=save_text, width=15,
            command=self.save,
            style="Publish.TButton"
        ).pack(side=tk.LEFT, padx=5)

    def save(self):
        """Сохранить сотрудника"""
        fio = self.fio_var.get().strip()
        position = self.position_var.get().strip()
        department = self.department_var.get()
        email = self.email_var.get().strip()

        # Валидация
        if not fio:
            messagebox.showerror("Ошибка", "Введите ФИО")
            return

        if not position:
            messagebox.showerror("Ошибка", "Введите должность")
            return

        if not email:
            messagebox.showerror("Ошибка", "Введите email")
            return

        # Сохраняем
        if self.employee:
            # Редактирование
            success = update_employee(self.employee['id'], fio, position, department, email)
            msg = "Данные сотрудника обновлены"
        else:
            # Добавление
            success = add_employee(fio, position, department, email)
            msg = "Сотрудник добавлен"

        if success:
            messagebox.showinfo("Успех", msg)
            self.employees_window.load_employees_list()
            self.dialog.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить данные")


class FamiliarizationDialog:
    """Диалог создания листа ознакомления для документа"""

    def __init__(self, parent, document):
        self.document = document

        # Создаём диалоговое окно
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Лист ознакомления")
        self.dialog.geometry("700x600")
        self.dialog.configure(bg="#2C3E50")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Загружаем сотрудников
        self.employees = load_employees()
        self.employee_vars = {}  # {employee_id: BooleanVar}

        self.create_widgets()

    def create_widgets(self):
        """Создание элементов диалога"""

        # Заголовок
        tk.Label(
            self.dialog, text="📄 Создание листа ознакомления",
            font=("Arial", 16, "bold"), bg="#37474F", fg="white", pady=10
        ).pack(fill=tk.X)

        # Информация о документе
        from logic import build_filename
        if self.document.is_valid:
            doc_name = build_filename(self.document.typ, self.document.kod,
                                     self.document.version, self.document.year, self.document.title)
        else:
            doc_name = self.document.filename

        doc_frame = tk.LabelFrame(
            self.dialog, text="Документ",
            padx=10, pady=10, font=("Arial", 12, "bold"),
            bg="#37474F", fg="white"
        )
        doc_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(
            doc_frame, text=doc_name,
            font=("Arial", 12), bg="#37474F", fg="white", wraplength=650
        ).pack(anchor="w")

        if hasattr(self.document, 'category') and self.document.category:
            tk.Label(
                doc_frame, text=f"Категория: {self.document.category}",
                font=("Arial", 10), bg="#37474F", fg="#B0BEC5"
            ).pack(anchor="w")

        # Кнопки быстрого выбора
        quick_frame = tk.Frame(self.dialog, bg="#455A64", pady=10)
        quick_frame.pack(fill=tk.X, padx=10)

        tk.Label(
            quick_frame, text="Быстрый выбор:",
            font=("Arial", 12, "bold"), bg="#455A64", fg="white"
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            quick_frame, text="Все ФБП", width=12,
            command=lambda: self.select_by_department("ФБП"),
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            quick_frame, text="Все НПФ", width=12,
            command=lambda: self.select_by_department("НПФ"),
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            quick_frame, text="Снять все", width=12,
            command=self.deselect_all,
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            quick_frame, text="Выбрать все", width=12,
            command=self.select_all,
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        # Список сотрудников с галочками
        emp_frame = tk.LabelFrame(
            self.dialog, text="Выберите сотрудников для ознакомления",
            padx=10, pady=10, font=("Arial", 12, "bold"),
            bg="#37474F", fg="white"
        )
        emp_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollable canvas
        canvas = tk.Canvas(emp_frame, bg="#37474F", highlightthickness=0)
        scrollbar = tk.Scrollbar(emp_frame, orient="vertical", command=canvas.yview, bg="#4A5568")
        self.scrollable_frame = tk.Frame(canvas, bg="#37474F")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Создаём галочки для каждого сотрудника
        if not self.employees:
            tk.Label(
                self.scrollable_frame, text="Нет сотрудников в справочнике",
                fg="#B0BEC5", font=("Arial", 12, "italic"), bg="#37474F"
            ).pack(pady=20)
        else:
            for emp in self.employees:
                emp_row = tk.Frame(self.scrollable_frame, bg="#4A5568", pady=5, padx=10)
                emp_row.pack(fill=tk.X, pady=2)

                var = tk.BooleanVar(value=False)
                self.employee_vars[emp['id']] = var

                chk = tk.Checkbutton(
                    emp_row, variable=var,
                    font=("Arial", 11), bg="#4A5568", fg="white",
                    selectcolor="#37474F", activebackground="#4A5568",
                    text=""
                )
                chk.pack(side=tk.LEFT, padx=5)

                # Информация о сотруднике
                info_text = f"{emp['fio']} — {emp['position']} ({emp['department']})"
                tk.Label(
                    emp_row, text=info_text,
                    font=("Arial", 11), bg="#4A5568", fg="white", anchor="w"
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Кнопки
        button_frame = tk.Frame(self.dialog, bg="#2C3E50")
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame, text="Отмена", width=15,
            command=self.dialog.destroy,
            style="TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, text="Создать лист", width=15,
            command=self.create_sheet,
            style="Publish.TButton"
        ).pack(side=tk.LEFT, padx=5)

    def select_by_department(self, department):
        """Выбрать всех сотрудников из подразделения"""
        for emp in self.employees:
            if emp['department'] == department:
                self.employee_vars[emp['id']].set(True)

    def deselect_all(self):
        """Снять все галочки"""
        for var in self.employee_vars.values():
            var.set(False)

    def select_all(self):
        """Выбрать всех сотрудников"""
        for var in self.employee_vars.values():
            var.set(True)

    def create_sheet(self):
        """Создать лист ознакомления"""
        # Получаем выбранных сотрудников
        selected = [emp for emp in self.employees if self.employee_vars[emp['id']].get()]

        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите хотя бы одного сотрудника")
            return

        # Диалог сохранения файла
        from logic import build_filename
        if self.document.is_valid:
            doc_short = f"{self.document.typ}.{self.document.kod}"
        else:
            doc_short = "Документ"

        default_name = f"Лист_ознакомления_{doc_short}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        filepath = filedialog.asksaveasfilename(
            title="Сохранить лист ознакомления",
            defaultextension=".xlsx",
            filetypes=[("Excel файлы", "*.xlsx"), ("Все файлы", "*.*")],
            initialfile=default_name
        )

        if not filepath:
            return

        # Создаём лист
        success = create_familiarization_sheet(self.document, selected, filepath)

        if success:
            messagebox.showinfo("Успех",
                f"Лист ознакомления создан!\n\n"
                f"Документ: {self.document.filename}\n"
                f"Сотрудников: {len(selected)}\n"
                f"Файл: {filepath}")
            self.dialog.destroy()
        else:
            messagebox.showerror("Ошибка",
                "Не удалось создать лист ознакомления.\n"
                "Убедитесь что установлена библиотека openpyxl:\n"
                "pip install openpyxl")