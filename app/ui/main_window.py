from __future__ import annotations

import csv
import random
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from app.core.checker import check_task_answer
from app.core.progress import get_topic_grade_stats, get_topic_stats, update_progress
from app.core.tasks_loader import Task, get_available_grades, get_topics_for_grade, load_tasks


class MainMenuFrame(ttk.Frame):
    def __init__(self, master, on_start, on_show_progress):
        super().__init__(master)
        self.on_start = on_start
        self.on_show_progress = on_show_progress

        self.grade_var = tk.IntVar(value=5)
        self.topic_var = tk.StringVar()
        self.difficulty_var = tk.StringVar(value="Любая")
        self.count_var = tk.StringVar(value="10")

        ttk.Label(self, text="Выбери класс:").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.grade_combo = ttk.Combobox(self, textvariable=self.grade_var, state="readonly", width=10)
        grades = get_available_grades() or [5]
        self.grade_combo["values"] = grades
        self.grade_combo.set(grades[0])
        self.grade_combo.grid(row=0, column=1, sticky="w", padx=8, pady=4)
        self.grade_combo.bind("<<ComboboxSelected>>", self._on_grade_changed)

        ttk.Label(self, text="Тема:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.topic_combo = ttk.Combobox(self, textvariable=self.topic_var, state="readonly", width=30)
        self.topic_combo.grid(row=1, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(self, text="Сложность:").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.difficulty_combo = ttk.Combobox(
            self,
            textvariable=self.difficulty_var,
            state="readonly",
            width=30,
            values=["Любая", "1: легко", "2: средне", "3: сложно"],
        )
        self.difficulty_combo.grid(row=2, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(self, text="Сколько задач за сессию:").grid(row=3, column=0, sticky="w", padx=8, pady=4)
        self.count_combo = ttk.Combobox(
            self,
            textvariable=self.count_var,
            state="readonly",
            width=30,
            values=["5", "10", "20", "Все"],
        )
        self.count_combo.grid(row=3, column=1, sticky="w", padx=8, pady=4)
        self.count_combo.set("10")

        self._refresh_topics()

        start_btn = ttk.Button(self, text="Начать тренировку", command=self._start_clicked)
        start_btn.grid(row=4, column=0, columnspan=2, pady=(12, 4), padx=8, sticky="ew")

        progress_btn = ttk.Button(self, text="Показать прогресс", command=self.on_show_progress)
        progress_btn.grid(row=5, column=0, columnspan=2, pady=(4, 8), padx=8, sticky="ew")

        for i in range(2):
            self.columnconfigure(i, weight=1)

    def _on_grade_changed(self, event=None):
        self._refresh_topics()

    def _refresh_topics(self):
        grade = int(self.grade_var.get())
        topics = get_topics_for_grade(grade)
        if not topics:
            topics = ["арифметика"]
        self.topic_combo["values"] = topics
        self.topic_combo.set(topics[0])

    def _parse_difficulty(self) -> Optional[int]:
        value = self.difficulty_var.get()
        if value == "Любая":
            return None
        try:
            number_part = value.split(":", 1)[0].strip()
            return int(number_part)
        except ValueError:
            return None

    def _parse_count(self) -> Optional[int]:
        value = self.count_var.get()
        if value == "Все":
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def _start_clicked(self):
        grade = int(self.grade_var.get())
        topic = self.topic_var.get()
        difficulty = self._parse_difficulty()
        count = self._parse_count()
        self.on_start(grade, topic, difficulty, count)


class TaskFrame(ttk.Frame):
    def __init__(self, master, on_back_to_menu, on_show_progress):
        super().__init__(master)
        self.on_back_to_menu = on_back_to_menu
        self.on_show_progress = on_show_progress
        self.tasks: List[Task] = []
        self.current_index: int = 0
        self._wrong_attempts: int = 0

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

    def start_session(self, tasks: List[Task]):
        self.tasks = tasks[:]
        random.shuffle(self.tasks)
        self.current_index = 0
        self._wrong_attempts = 0
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
        header = f"Класс {task.grade}, тема: {task.topic} (сложность {task.difficulty})\n\n"
        self.task_label.config(text=header + task.text)

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
        update_progress(task, is_correct)
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

        ttk.Label(self, text="Прогресс по темам и классам").grid(row=0, column=0, sticky="w", padx=8, pady=8)

        self.tree = ttk.Treeview(
            self,
            columns=("grade", "topic", "attempts", "success"),
            show="headings",
            height=8,
        )
        self.tree.heading("grade", text="Класс")
        self.tree.heading("topic", text="Тема")
        self.tree.heading("attempts", text="Попыток")
        self.tree.heading("success", text="Успешность")
        self.tree.column("grade", width=60, anchor="center")
        self.tree.column("topic", width=200)
        self.tree.column("attempts", width=80, anchor="center")
        self.tree.column("success", width=100, anchor="center")
        self.tree.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=4)
        self.tree.configure(yscrollcommand=scrollbar.set)

        btn_back = ttk.Button(self, text="Назад в меню", command=self.on_back)
        btn_back.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 8))

        btn_export = ttk.Button(self, text="Экспорт CSV", command=self.export_csv)
        btn_export.grid(row=2, column=1, sticky="ew", padx=8, pady=(4, 8))

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

    def refresh(self):
        # загружаем все задачи, чтобы корректно посчитать статистику по темам и классам
        from app.core.tasks_loader import load_tasks

        all_tasks = load_tasks()
        stats = get_topic_grade_stats(all_tasks)

        for row in self.tree.get_children():
            self.tree.delete(row)
        for (grade, topic), tp in sorted(stats.items()):
            percent = int(tp.success_rate * 100)
            self.tree.insert("", "end", values=(grade, topic, tp.attempts, f"{percent}%"))

    def export_csv(self):
        from app.core.tasks_loader import load_tasks

        all_tasks = load_tasks()
        stats = get_topic_grade_stats(all_tasks)
        if not stats:
            messagebox.showinfo("Экспорт", "Пока нет данных для экспорта.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Сохранить статистику",
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
        )
        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Класс", "Тема", "Попыток", "Успешность (%)"])
            for (grade, topic), tp in sorted(stats.items()):
                percent = int(tp.success_rate * 100)
                writer.writerow([grade, topic, tp.attempts, percent])

        messagebox.showinfo("Экспорт", f"Статистика сохранена в файл:\n{file_path}")


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
        tasks = load_tasks(grade=grade, topic=topic)

        if difficulty is not None:
            tasks = [t for t in tasks if t.difficulty == difficulty]

        # адаптивная сложность только если не задана явно
        if tasks and difficulty is None:
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

        if count is not None and len(tasks) > count:
            tasks = random.sample(tasks, k=count)

        self.task_frame.tkraise()
        self.task_frame.start_session(tasks)

    def show_progress(self):
        self.progress_frame.refresh()
        self.progress_frame.tkraise()


def run():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    run()

