"""
GUI для ISO2
Главное окно с реестром документов и диалог публикации
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from config import PROJECTS_DIR, ACTIVE_DIR, ARCHIVE_DIR, CATEGORIES, ACTIVE_CATEGORIES, ARCHIVE_CATEGORIES
from logic import (
    scan_folder, scan_folder_with_categories, find_similar_documents, compare_documents,
    publish_document, parse_filename, build_filename
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

        # Разделитель
        tk.Frame(top_frame, width=30, bg="#37474F").pack(side=tk.LEFT)

        # Кнопка публикации
        self.publish_btn = ttk.Button(
            top_frame, text="📤 Опубликовать", width=20,
            command=self.open_publish_dialog,
            style="Publish.TButton"
        )
        self.publish_btn.pack(side=tk.LEFT, padx=5)

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
            os.startfile(doc.full_path)

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