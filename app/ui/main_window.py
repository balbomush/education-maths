from __future__ import annotations

import csv
import random
import re
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from app.core.checker import check_task_answer
from app.core.progress import (
    get_recent_task_ids_for_topic,
    get_sessions,
    get_session_task_stats,
    get_topic_grade_stats,
    get_topic_stats,
    start_session,
    update_progress,
)
from app.core.tasks_loader import Task, load_tasks


class MainMenuFrame(ttk.Frame):
    def __init__(self, master, on_start, on_show_progress):
        super().__init__(master)
        self.on_start = on_start
        self.on_show_progress = on_show_progress

        self.topic_var = tk.StringVar()
        self.count_var = tk.StringVar(value="10")

        ttk.Label(self, text="Тема:").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.topic_combo = ttk.Combobox(self, textvariable=self.topic_var, state="readonly", width=40)
        self.topic_combo.grid(row=0, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(self, text="Сколько задач за сессию:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.count_combo = ttk.Combobox(
            self,
            textvariable=self.count_var,
            state="readonly",
            width=30,
            values=["5", "10", "20", "Все"],
        )
        self.count_combo.grid(row=1, column=1, sticky="w", padx=8, pady=4)
        self.count_combo.set("10")

        self._init_topics()

        start_btn = ttk.Button(self, text="Начать тренировку", command=self._start_clicked)
        start_btn.grid(row=2, column=0, columnspan=2, pady=(12, 4), padx=8, sticky="ew")

        progress_btn = ttk.Button(self, text="Показать прогресс", command=self.on_show_progress)
        progress_btn.grid(row=3, column=0, columnspan=2, pady=(4, 8), padx=8, sticky="ew")

        for i in range(2):
            self.columnconfigure(i, weight=1)

    def _init_topics(self):
        """Собирает список всех тем из банка задач (без выбора класса)."""
        all_tasks = load_tasks()
        topics = sorted({t.topic for t in all_tasks})
        if not topics:
            topics = ["арифметика"]
        self.topic_combo["values"] = topics
        self.topic_combo.set(topics[0])

    def _parse_count(self) -> Optional[int]:
        value = self.count_var.get()
        if value == "Все":
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def _start_clicked(self):
        topic = self.topic_var.get()
        count = self._parse_count()
        # grade не используем — работаем по всем классам для выбранной темы
        self.on_start(None, topic, None, count)


class TaskFrame(ttk.Frame):
    def __init__(self, master, on_back_to_menu, on_show_progress):
        super().__init__(master)
        self.on_back_to_menu = on_back_to_menu
        self.on_show_progress = on_show_progress
        self.tasks: List[Task] = []
        self.current_index: int = 0
        self._wrong_attempts: int = 0
        self.session_id: Optional[str] = None

        self.task_label = ttk.Label(self, text="", wraplength=500, justify="left")
        self.task_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=8)

        self.answer_var = tk.StringVar()
        self.answer_entry = ttk.Entry(self, textvariable=self.answer_var, width=30)
        # по умолчанию поле видимо; для задач с выбором ответов будем скрывать
        self.answer_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=4)

        # отдельный блок для вариантов ответа (чекбоксы / радиокнопки)
        self.options_frame = ttk.Frame(self)
        self.options_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=4)

        self.options_vars: List[tk.BooleanVar] = []
        self.options_checks: List[ttk.Checkbutton] = []

        self.feedback_label = ttk.Label(self, text="", foreground="blue")
        self.feedback_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=4)

        btn_check = ttk.Button(self, text="Проверить", command=self.check_answer)
        btn_check.grid(row=4, column=0, sticky="ew", padx=8, pady=4)

        btn_hint = ttk.Button(self, text="Подсказка", command=self._show_hint)
        btn_hint.grid(row=4, column=1, sticky="ew", padx=8, pady=4)

        btn_back = ttk.Button(self, text="В меню", command=self.on_back_to_menu)
        btn_back.grid(row=5, column=0, sticky="ew", padx=8, pady=(4, 8))

        btn_progress = ttk.Button(self, text="Прогресс", command=self.on_show_progress)
        btn_progress.grid(row=5, column=1, sticky="ew", padx=8, pady=(4, 8))

        for i in range(2):
            self.columnconfigure(i, weight=1)

    def start_session(self, tasks: List[Task], session_id: Optional[str] = None):
        self.tasks = tasks[:]
        random.shuffle(self.tasks)
        self.current_index = 0
        self._wrong_attempts = 0
        self.session_id = session_id
        if not self.tasks:
            messagebox.showinfo("Нет задач", "Для выбранного класса и темы пока нет задач.")
            self.on_back_to_menu()
            return
        self._show_current_task()

    def _clear_options(self):
        for child in self.options_frame.winfo_children():
            child.destroy()
        self.options_checks.clear()
        self.options_vars.clear()

    def _show_current_task(self):
        self.feedback_label.config(text="")
        self.answer_var.set("")
        self._clear_options()
        self._wrong_attempts = 0

        task = self.tasks[self.current_index]

        # лёгкое форматирование дробей в тексте (1/2 -> 1⁄2)
        display_text = re.sub(r"(\d+)\s*/\s*(\d+)", r"\1⁄\2", task.text)
        # корректный вид выражений с отрицательными числами: 5x + -8 -> 5x - 8
        display_text = display_text.replace("+ -", "- ").replace("- -", "+ ")

        header = f"Тема: {task.topic} (класс {task.grade}, сложность {task.difficulty})\n\n"
        self.task_label.config(text=header + display_text)

        if task.answer_type == "multiple_choice" and task.options:
            # для задач с выбором вариантов убираем текстовое поле
            self.answer_entry.grid_remove()
            for idx, opt in enumerate(task.options):
                var = tk.BooleanVar(value=False)
                chk = ttk.Checkbutton(self.options_frame, text=opt, variable=var)
                chk.grid(row=idx, column=0, sticky="w", padx=8, pady=2)
                self.options_vars.append(var)
                self.options_checks.append(chk)
        else:
            # для числовых/текстовых задач поле ввода обязательно
            if not self.answer_entry.winfo_ismapped():
                self.answer_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=4)

        # фокус ставим на первый доступный элемент ввода
        if task.answer_type == "multiple_choice" and self.options_checks:
            self.options_checks[0].focus_set()
        else:
            self.answer_entry.focus_set()

    def _collect_user_input(self, task: Task):
        if task.answer_type == "multiple_choice" and task.options:
            indices = [i for i, var in enumerate(self.options_vars) if var.get()]
            return indices
        return self.answer_var.get()

    def check_answer(self, event=None):
        if not self.tasks:
            return
        task = self.tasks[self.current_index]
        user_input = self._collect_user_input(task)
        is_correct, feedback = check_task_answer(task, user_input)
        self.feedback_label.config(text=feedback, foreground="green" if is_correct else "red")
        update_progress(task, is_correct, session_id=self.session_id)
        if is_correct:
            self._wrong_attempts = 0
            self.after(700, self._next_task)
        else:
            self._wrong_attempts += 1
            if self._wrong_attempts >= 2 and task.solution_hint:
                messagebox.showinfo("Разбор", task.solution_hint)

    def _next_task(self):
        if not self.tasks:
            return
        self.current_index += 1
        if self.current_index >= len(self.tasks):
            messagebox.showinfo("Сессия завершена", "Задачи для этой тренировки закончились!")
            self.on_back_to_menu()
        else:
            self._show_current_task()

    def _show_hint(self, event=None):
        if not self.tasks:
            return
        task = self.tasks[self.current_index]
        if task.solution_hint:
            messagebox.showinfo("Подсказка", task.solution_hint)
        else:
            messagebox.showinfo("Подсказка", "Для этой задачи подсказка не задана.")


class ProgressFrame(ttk.Frame):
    def __init__(self, master, on_back):
        super().__init__(master)
        self.on_back = on_back

        ttk.Label(self, text="Прогресс").grid(row=0, column=0, sticky="w", padx=8, pady=8)

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=4)

        # Вкладка сводки по темам
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="По темам")

        self.summary_tree = ttk.Treeview(
            self.summary_frame,
            columns=("grade", "topic", "attempts", "success"),
            show="headings",
            height=8,
        )
        self.summary_tree.heading("grade", text="Класс")
        self.summary_tree.heading("topic", text="Тема")
        self.summary_tree.heading("attempts", text="Попыток")
        self.summary_tree.heading("success", text="Успешность")
        self.summary_tree.column("grade", width=60, anchor="center")
        self.summary_tree.column("topic", width=200)
        self.summary_tree.column("attempts", width=80, anchor="center")
        self.summary_tree.column("success", width=100, anchor="center")
        self.summary_tree.grid(row=0, column=0, sticky="nsew")

        summary_scroll = ttk.Scrollbar(self.summary_frame, orient="vertical", command=self.summary_tree.yview)
        summary_scroll.grid(row=0, column=1, sticky="ns")
        self.summary_tree.configure(yscrollcommand=summary_scroll.set)

        self.summary_frame.columnconfigure(0, weight=1)
        self.summary_frame.rowconfigure(0, weight=1)

        # Вкладка сессий
        self.sessions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sessions_frame, text="Сессии")

        self.sessions_tree = ttk.Treeview(
            self.sessions_frame,
            columns=("date", "topic", "tasks", "success"),
            show="headings",
            height=8,
        )
        self.sessions_tree.heading("date", text="Дата")
        self.sessions_tree.heading("topic", text="Тема")
        self.sessions_tree.heading("tasks", text="Задач")
        self.sessions_tree.heading("success", text="Успешность")
        self.sessions_tree.column("date", width=110, anchor="center")
        self.sessions_tree.column("topic", width=200)
        self.sessions_tree.column("tasks", width=70, anchor="center")
        self.sessions_tree.column("success", width=100, anchor="center")
        self.sessions_tree.grid(row=0, column=0, sticky="nsew")

        sessions_scroll = ttk.Scrollbar(self.sessions_frame, orient="vertical", command=self.sessions_tree.yview)
        sessions_scroll.grid(row=0, column=1, sticky="ns")
        self.sessions_tree.configure(yscrollcommand=sessions_scroll.set)

        self.sessions_frame.columnconfigure(0, weight=1)
        self.sessions_frame.rowconfigure(0, weight=1)

        btn_back = ttk.Button(self, text="Назад в меню", command=self.on_back)
        btn_back.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 8))

        btn_export = ttk.Button(self, text="Экспорт CSV (с задачами)", command=self.export_csv)
        btn_export.grid(row=2, column=1, sticky="ew", padx=8, pady=(4, 8))

        btn_session_details = ttk.Button(self, text="Показать задачи сессии", command=self.show_session_details)
        btn_session_details.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

    def refresh(self):
        # загружаем все задачи, чтобы корректно посчитать статистику по темам и классам
        from app.core.tasks_loader import load_tasks

        all_tasks = load_tasks()
        stats = get_topic_grade_stats(all_tasks)

        for row in self.summary_tree.get_children():
            self.summary_tree.delete(row)
        for (grade, topic), tp in sorted(stats.items()):
            percent = int(tp.success_rate * 100)
            self.summary_tree.insert("", "end", values=(grade, topic, tp.attempts, f"{percent}%"))

        # обновляем список сессий
        for row in self.sessions_tree.get_children():
            self.sessions_tree.delete(row)

        sessions = get_sessions()
        for session in sorted(sessions, key=lambda s: s.get("started_at", ""), reverse=True):
            sid = session.get("id")
            started_at = session.get("started_at", "")
            date = started_at.split("T")[0] if "T" in started_at else started_at
            topic = session.get("topic", "")
            stasks = session.get("tasks", {})
            attempts = 0
            correct = 0
            for rec in stasks.values():
                attempts += int(rec.get("attempts", 0))
                correct += int(rec.get("correct_attempts", 0))
            success = int((correct / attempts) * 100) if attempts else 0
            self.sessions_tree.insert(
                "",
                "end",
                iid=sid,
                values=(date, topic, len(stasks), f"{success}%"),
            )

    def export_csv(self):
        from app.core.tasks_loader import load_tasks

        all_tasks = load_tasks()
        stats = get_topic_grade_stats(all_tasks)
        file_path = filedialog.asksaveasfilename(
            title="Сохранить статистику",
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
        )
        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            # Сводка по темам
            writer.writerow(["Класс", "Тема", "Попыток", "Успешность (%)"])
            for (grade, topic), tp in sorted(stats.items()):
                percent = int(tp.success_rate * 100)
                writer.writerow([grade, topic, tp.attempts, percent])

            # Пустая строка-разделитель
            writer.writerow([])

            # Подробности по задачам внутри сессий
            writer.writerow(
                [
                    "Дата",
                    "ID сессии",
                    "Тема сессии",
                    "ID задачи",
                    "Класс задачи",
                    "Тема задачи",
                    "Текст задачи",
                    "Попыток",
                    "Верных",
                    "Успешность (%)",
                ]
            )

            all_tasks_map = {t.id: t for t in all_tasks}
            sessions = get_sessions()
            for session in sorted(sessions, key=lambda s: s.get("started_at", ""), reverse=True):
                sid = session.get("id")
                started_at = session.get("started_at", "")
                date = started_at.split("T")[0] if "T" in started_at else started_at
                topic = session.get("topic", "")
                per_task = get_session_task_stats(sid)
                for task_id, tp in per_task.items():
                    task = all_tasks_map.get(task_id)
                    if not task:
                        continue
                    percent = int(tp.success_rate * 100) if tp.attempts else 0
                    writer.writerow(
                        [
                            date,
                            sid,
                            topic,
                            task.id,
                            task.grade,
                            task.topic,
                            task.text,
                            tp.attempts,
                            tp.correct_attempts,
                            percent,
                        ]
                    )

        messagebox.showinfo("Экспорт", f"Статистика сохранена в файл:\n{file_path}")

    def show_session_details(self):
        """Открывает окно с подробностями по выбранной сессии."""
        selection = self.sessions_tree.selection()
        if not selection:
            messagebox.showinfo("Сессии", "Сначала выбери сессию в списке.")
            return
        session_id = selection[0]
        task_stats = get_session_task_stats(session_id)
        if not task_stats:
            messagebox.showinfo("Сессии", "Нет данных по задачам для выбранной сессии.")
            return

        from app.core.tasks_loader import load_tasks

        all_tasks = {t.id: t for t in load_tasks()}

        window = tk.Toplevel(self)
        window.title("Задачи сессии")
        window.geometry("700x400")

        tree = ttk.Treeview(
            window,
            columns=("id", "grade", "topic", "text", "attempts", "success"),
            show="headings",
            height=12,
        )
        tree.heading("id", text="ID")
        tree.heading("grade", text="Класс")
        tree.heading("topic", text="Тема")
        tree.heading("text", text="Задача")
        tree.heading("attempts", text="Попыток")
        tree.heading("success", text="Успешность")
        tree.column("id", width=80, anchor="center")
        tree.column("grade", width=60, anchor="center")
        tree.column("topic", width=150)
        tree.column("text", width=260)
        tree.column("attempts", width=80, anchor="center")
        tree.column("success", width=100, anchor="center")
        tree.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        scrollbar = ttk.Scrollbar(window, orient="vertical", command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=8)
        tree.configure(yscrollcommand=scrollbar.set)

        for task_id, tp in task_stats.items():
            task = all_tasks.get(task_id)
            if not task:
                continue
            percent = int(tp.success_rate * 100) if tp.attempts else 0
            # укороченный текст задачи для списка
            text_short = task.text
            if len(text_short) > 80:
                text_short = text_short[:77] + "..."
            tree.insert(
                "",
                "end",
                values=(task.id, task.grade, task.topic, text_short, tp.attempts, f"{percent}%"),
            )

        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Задачи по математике")
        self.geometry("700x520")

        # немного увеличим базовый шрифт интерфейса
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=12)
        self.option_add("*Font", default_font)

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}

        self.main_menu = MainMenuFrame(
            container,
            on_start=self.start_training,
            on_show_progress=self.show_progress,
        )
        self.main_menu.grid(row=0, column=0, sticky="nsew")

        self.task_frame = TaskFrame(
            container,
            on_back_to_menu=self.show_main_menu,
            on_show_progress=self.show_progress,
        )
        self.task_frame.grid(row=0, column=0, sticky="nsew")

        self.progress_frame = ProgressFrame(
            container,
            on_back=self.show_main_menu,
        )
        self.progress_frame.grid(row=0, column=0, sticky="nsew")

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # горячие клавиши
        self.bind("<Return>", self.task_frame.check_answer)
        self.bind("<Control-h>", self.task_frame._show_hint)
        self.bind("<Escape>", lambda event: self.show_main_menu())

        self.show_main_menu()

    def show_main_menu(self):
        self.main_menu.tkraise()

    def start_training(self, grade: int, topic: str, difficulty: Optional[int], count: Optional[int]):
        # загружаем все задачи выбранной темы из всех классов
        tasks = load_tasks(topic=topic)

        # адаптивная сложность: выбираем "целевую" сложность по статистике
        if tasks:
            topic_stats = get_topic_stats(tasks)
            tp = topic_stats.get(topic)
            if tp:
                rate = tp.success_rate
                if rate > 0.8:
                    target_diff = 3
                elif rate < 0.5:
                    target_diff = 1
                else:
                    target_diff = 2
                tasks.sort(key=lambda t: abs(t.difficulty - target_diff))

        # избегаем недавних задач этой темы
        recent_ids = get_recent_task_ids_for_topic(topic, max_sessions=3)
        fresh_tasks = [t for t in tasks if t.id not in recent_ids]

        if count is not None:
            # если свежих задач меньше, чем нужно, дополним их старыми
            if len(fresh_tasks) >= count:
                tasks_for_session = random.sample(fresh_tasks, k=count)
            else:
                remaining = count - len(fresh_tasks)
                old_tasks = [t for t in tasks if t.id in recent_ids]
                if len(old_tasks) > remaining:
                    old_tasks = random.sample(old_tasks, k=remaining)
                tasks_for_session = fresh_tasks + old_tasks
        else:
            tasks_for_session = fresh_tasks or tasks

        # создаём новую сессию
        session_id = start_session(topic)

        self.task_frame.tkraise()
        self.task_frame.start_session(tasks_for_session, session_id=session_id)

    def show_progress(self):
        self.progress_frame.refresh()
        self.progress_frame.tkraise()


def run():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    run()

