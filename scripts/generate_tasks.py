from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, List


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


@dataclass
class TaskDef:
    id: str
    grade: int
    topic: str
    text: str
    answer_type: str
    correct_answer: Any
    difficulty: int
    solution_hint: str
    options: Any = None


def make_id(grade: int, idx: int) -> str:
    return f"{grade}_{idx:03d}"


def generate_grade5() -> List[TaskDef]:
    tasks: List[TaskDef] = []
    idx = 1

    # сложение и вычитание натуральных чисел
    for a in range(10, 100, 7):
        for b in range(2, 20, 3):
            if len(tasks) >= 25:
                break
            text = f"Вычисли: {a} + {b}"
            tasks.append(
                TaskDef(
                    id=make_id(5, idx),
                    grade=5,
                    topic="сложение и вычитание",
                    text=text,
                    answer_type="numeric",
                    correct_answer=a + b,
                    difficulty=1,
                    solution_hint="Сложи десятки и единицы по отдельности.",
                )
            )
            idx += 1
        if len(tasks) >= 25:
            break

    for a in range(30, 130, 9):
        for b in range(5, 25, 4):
            if len(tasks) >= 50:
                break
            if a <= b:
                continue
            text = f"Вычисли: {a} - {b}"
            tasks.append(
                TaskDef(
                    id=make_id(5, idx),
                    grade=5,
                    topic="сложение и вычитание",
                    text=text,
                    answer_type="numeric",
                    correct_answer=a - b,
                    difficulty=1,
                    solution_hint="Вычитай десятки и единицы по отдельности.",
                )
            )
            idx += 1
        if len(tasks) >= 50:
            break

    # умножение и деление
    for a in range(3, 10):
        for b in range(4, 10):
            if len(tasks) >= 75:
                break
            text = f"Найди значение выражения: {a} × {b}"
            tasks.append(
                TaskDef(
                    id=make_id(5, idx),
                    grade=5,
                    topic="умножение и деление",
                    text=text,
                    answer_type="numeric",
                    correct_answer=a * b,
                    difficulty=1,
                    solution_hint="Используй таблицу умножения.",
                )
            )
            idx += 1
        if len(tasks) >= 75:
            break

    for a in range(40, 160, 8):
        for b in (2, 4, 5, 8):
            if len(tasks) >= 90:
                break
            text = f"Вычисли: {a} : {b}"
            tasks.append(
                TaskDef(
                    id=make_id(5, idx),
                    grade=5,
                    topic="умножение и деление",
                    text=text,
                    answer_type="numeric",
                    correct_answer=a // b,
                    difficulty=2,
                    solution_hint="Раздели сначала десятки, затем единицы или подели в столбик.",
                )
            )
            idx += 1
        if len(tasks) >= 90:
            break

    # простые текстовые задачи
    word_problems = [
        ("В коробке было 15 карандашей. 7 карандашей раздали. Сколько карандашей осталось?", 15, 7),
        ("В одной стопке 24 тетради, а в другой на 8 тетрадей больше. Сколько тетрадей во второй стопке?", 24, 8),
        ("На дереве сидело 18 воробьёв, 5 улетели. Сколько воробьёв осталось?", 18, 5),
        ("В классе 12 мальчиков и 13 девочек. Сколько всего учеников в классе?", 12, 13),
        ("У Маши было 20 конфет, она отдала подруге 9. Сколько конфет осталось у Маши?", 20, 9),
    ]
    for base_text, x, y in word_problems:
        tasks.append(
            TaskDef(
                id=make_id(5, idx),
                grade=5,
                topic="текстовые задачи",
                text=base_text,
                answer_type="numeric",
                correct_answer=x - y if x > y else x + y,
                difficulty=2,
                solution_hint="Составь выражение по условию задачи и реши его.",
            )
        )
        idx += 1

    # добиваем до минимум 500 задач на каждую тему (topic)
    def topic_count(name: str) -> int:
        return sum(1 for t in tasks if t.topic == name)

    # сложение и вычитание
    while topic_count("сложение и вычитание") < 500:
        a = 10 + (idx * 7) % 90
        b = 1 + (idx * 5) % 50
        if idx % 2 == 0:
            text = f"Вычисли: {a} + {b}"
            correct = a + b
            hint = "Сложи с учётом разрядов."
        else:
            if a <= b:
                a, b = b + 10, a
            text = f"Вычисли: {a} - {b}"
            correct = a - b
            hint = "Выполни вычитание в столбик."
        tasks.append(
            TaskDef(
                id=make_id(5, idx),
                grade=5,
                topic="сложение и вычитание",
                text=text,
                answer_type="numeric",
                correct_answer=correct,
                difficulty=1,
                solution_hint=hint,
            )
        )
        idx += 1

    # умножение и деление
    while topic_count("умножение и деление") < 500:
        a = 2 + (idx * 3) % 90
        b = 2 + (idx * 5) % 9
        if idx % 2 == 0:
            text = f"Вычисли: {a} × {b}"
            correct = a * b
            hint = "Перемножь десятки и единицы или используй таблицу умножения."
        else:
            prod = a * b
            text = f"Вычисли: {prod} : {b}"
            correct = a
            hint = "Подумай, какое число умножить на делитель, чтобы получить делимое."
        tasks.append(
            TaskDef(
                id=make_id(5, idx),
                grade=5,
                topic="умножение и деление",
                text=text,
                answer_type="numeric",
                correct_answer=correct,
                difficulty=2,
                solution_hint=hint,
            )
        )
        idx += 1

    # текстовые задачи
    while topic_count("текстовые задачи") < 500:
        apples = 10 + (idx * 4) % 90
        sold = 1 + (idx * 3) % max(1, apples // 2)
        text = (
            f"В коробке было {apples} карандашей. {sold} карандашей раздали. "
            "Сколько карандашей осталось в коробке?"
        )
        correct = apples - sold
        tasks.append(
            TaskDef(
                id=make_id(5, idx),
                grade=5,
                topic="текстовые задачи",
                text=text,
                answer_type="numeric",
                correct_answer=correct,
                difficulty=2,
                solution_hint="Переведи условие в выражение и реши его.",
            )
        )
        idx += 1

    return tasks


def generate_grade6() -> List[TaskDef]:
    tasks: List[TaskDef] = []
    idx = 1

    # дроби: сокращение и приведение к неправильной
    pairs = [(4, 8), (6, 9), (10, 25), (9, 12), (14, 21)]
    for num, den in pairs:
        text = f"Сократи дробь {num}/{den} до несократимого вида."
        tasks.append(
            TaskDef(
                id=make_id(6, idx),
                grade=6,
                topic="дроби",
                text=text,
                answer_type="numeric",
                correct_answer=f"{num // 2}/{den // 2}" if num % 2 == 0 and den % 2 == 0 else f"{num}/{den}",
                difficulty=2,
                solution_hint="Раздели числитель и знаменатель на их наибольший общий делитель.",
            )
        )
        idx += 1

    mixed = [(3, 1, 4), (2, 1, 3), (5, 2, 5)]
    for whole, num, den in mixed:
        improper_num = whole * den + num
        text = f"Представь число {whole} {num}/{den} в виде неправильной дроби."
        tasks.append(
            TaskDef(
                id=make_id(6, idx),
                grade=6,
                topic="дроби",
                text=text,
                answer_type="numeric",
                correct_answer=f"{improper_num}/{den}",
                difficulty=2,
                solution_hint="Умножь целую часть на знаменатель и прибавь числитель.",
            )
        )
        idx += 1

    # проценты
    percent_cases = [(100, 10), (200, 25), (150, 20), (80, 5), (90, 30)]
    for value, p in percent_cases:
        text = f"Найди {p}% от числа {value}."
        correct = value * p / 100
        tasks.append(
            TaskDef(
                id=make_id(6, idx),
                grade=6,
                topic="проценты",
                text=text,
                answer_type="numeric",
                correct_answer=correct,
                difficulty=2,
                solution_hint="Умножь число на процент и раздели на 100.",
            )
        )
        idx += 1

    # простые линейные уравнения
    eq_cases = [(8, 7), (15, 9), (21, 7), (30, 12)]
    for s, x in eq_cases:
        text = f"Реши уравнение: x + {x} = {s}. Введи значение x."
        tasks.append(
            TaskDef(
                id=make_id(6, idx),
                grade=6,
                topic="уравнения",
                text=text,
                answer_type="numeric",
                correct_answer=s - x,
                difficulty=1,
                solution_hint="Перенеси известное слагаемое в другую часть уравнения.",
            )
        )
        idx += 1

    for k, x in [(3, 21), (4, 32), (5, 45)]:
        text = f"Реши уравнение: {k}x = {x}. Введи значение x."
        tasks.append(
            TaskDef(
                id=make_id(6, idx),
                grade=6,
                topic="уравнения",
                text=text,
                answer_type="numeric",
                correct_answer=x // k,
                difficulty=2,
                solution_hint="Раздели обе части уравнения на коэффициент при x.",
            )
        )
        idx += 1

    def topic_count(name: str) -> int:
        return sum(1 for t in tasks if t.topic == name)

    # дроби
    while topic_count("дроби") < 500:
        num = 2 + (idx * 3) % 18
        den = 3 + (idx * 5) % 17
        g = math.gcd(num, den)
        text = f"Сократи дробь {num}/{den} до несократимого вида."
        correct = f"{num // g}/{den // g}"
        tasks.append(
            TaskDef(
                id=make_id(6, idx),
                grade=6,
                topic="дроби",
                text=text,
                answer_type="numeric",
                correct_answer=correct,
                difficulty=2,
                solution_hint="Раздели числитель и знаменатель на их наибольший общий делитель.",
            )
        )
        idx += 1

    # проценты
    while topic_count("проценты") < 500:
        value = 50 + (idx * 7) % 950
        p = 5 + (idx * 3) % 45
        text = f"Найди {p}% от числа {value}."
        correct = value * p / 100
        tasks.append(
            TaskDef(
                id=make_id(6, idx),
                grade=6,
                topic="проценты",
                text=text,
                answer_type="numeric",
                correct_answer=correct,
                difficulty=2,
                solution_hint="Умножь число на процент и раздели на 100.",
            )
        )
        idx += 1

    # уравнения
    while topic_count("уравнения") < 500:
        a = 2 + (idx * 2) % 9
        x_val = 1 + (idx * 3) % 30
        b = 1 + (idx * 5) % 20
        # уравнение вида ax + b = c
        c = a * x_val + b
        text = f"Реши уравнение: {a}x + {b} = {c}. Введи значение x."
        tasks.append(
            TaskDef(
                id=make_id(6, idx),
                grade=6,
                topic="уравнения",
                text=text,
                answer_type="numeric",
                correct_answer=x_val,
                difficulty=2,
                solution_hint="Перенеси свободный член и раздели на коэффициент при x.",
            )
        )
        idx += 1

    return tasks


def generate_grade7() -> List[TaskDef]:
    tasks: List[TaskDef] = []
    idx = 1

    # пропорции
    triples = [(2, 5, 8), (3, 4, 6), (5, 2, 15)]
    for a, b, c in triples:
        # a : b = c : x => x = b * c / a
        x = b * c / a
        text = f"Реши пропорцию: {a} : {b} = {c} : x. Найди x."
        tasks.append(
            TaskDef(
                id=make_id(7, idx),
                grade=7,
                topic="пропорции",
                text=text,
                answer_type="numeric",
                correct_answer=x,
                difficulty=2,
                solution_hint="Используй основное свойство пропорции: произведения крайних и средних членов равны.",
            )
        )
        idx += 1

    # проценты сложнее
    percent_cases = [(80, 15), (250, 18), (320, 12)]
    for value, p in percent_cases:
        text = f"Цена товара {value} руб. Её увеличили на {p}%. Сколько стала стоить товар?"
        new_price = value * (100 + p) / 100
        tasks.append(
            TaskDef(
                id=make_id(7, idx),
                grade=7,
                topic="проценты",
                text=text,
                answer_type="numeric",
                correct_answer=new_price,
                difficulty=2,
                solution_hint="Найди {p}% от числа и прибавь к исходной цене.".format(p=p),
            )
        )
        idx += 1

    # линейные уравнения
    eq_cases = [(2, 3, 11), (3, 4, 19), (5, -2, 18)]
    for a, b, c in eq_cases:
        # ax + b = c => x = (c - b) / a
        x = (c - b) / a
        text = f"Реши уравнение: {a}x + {b} = {c}. Введи значение x."
        tasks.append(
            TaskDef(
                id=make_id(7, idx),
                grade=7,
                topic="уравнения",
                text=text,
                answer_type="numeric",
                correct_answer=x,
                difficulty=2,
                solution_hint="Перенеси свободный член и раздели на коэффициент при x.",
            )
        )
        idx += 1

    def topic_count(name: str) -> int:
        return sum(1 for t in tasks if t.topic == name)

    # пропорции
    while topic_count("пропорции") < 500:
        a = 2 + (idx * 2) % 20
        b = 3 + (idx * 3) % 20
        c = 4 + (idx * 5) % 20
        x = b * c / a
        text = f"Реши пропорцию: {a} : {b} = {c} : x. Найди x."
        tasks.append(
            TaskDef(
                id=make_id(7, idx),
                grade=7,
                topic="пропорции",
                text=text,
                answer_type="numeric",
                correct_answer=x,
                difficulty=2,
                solution_hint="Используй основное свойство пропорции: произведения крайних и средних членов равны.",
            )
        )
        idx += 1

    # проценты
    while topic_count("проценты") < 500:
        value = 100 + (idx * 11) % 900
        p = 5 + (idx * 4) % 45
        text = f"Цена товара {value} руб. Её увеличили на {p}%. Сколько стала стоить товар?"
        new_price = value * (100 + p) / 100
        tasks.append(
            TaskDef(
                id=make_id(7, idx),
                grade=7,
                topic="проценты",
                text=text,
                answer_type="numeric",
                correct_answer=new_price,
                difficulty=2,
                solution_hint=f"Найди {p}% от числа и прибавь к исходной цене.",
            )
        )
        idx += 1

    # уравнения
    while topic_count("уравнения") < 500:
        a = 2 + (idx * 3) % 9
        b = -10 + (idx * 5) % 21
        x_val = -10 + (idx * 7) % 21
        c = a * x_val + b
        text = f"Реши уравнение: {a}x + {b} = {c}. Введи значение x."
        tasks.append(
            TaskDef(
                id=make_id(7, idx),
                grade=7,
                topic="уравнения",
                text=text,
                answer_type="numeric",
                correct_answer=x_val,
                difficulty=2,
                solution_hint="Перенеси свободный член и раздели на коэффициент при x.",
            )
        )
        idx += 1

    return tasks


def generate_grade8() -> List[TaskDef]:
    tasks: List[TaskDef] = []
    idx = 1

    # квадратные уравнения с целыми корнями
    cases = [(1, -5, 6), (1, -3, -4), (1, 2, -8)]
    for a, b, c in cases:
        text = f"Реши уравнение: {a}x² + {b}x + {c} = 0. Введи один из корней."
        # корни целые, перечислим вручную
        if (a, b, c) == (1, -5, 6):
            root = 2
        elif (a, b, c) == (1, -3, -4):
            root = 4
        else:
            root = 2
        tasks.append(
            TaskDef(
                id=make_id(8, idx),
                grade=8,
                topic="квадратные уравнения",
                text=text,
                answer_type="numeric",
                correct_answer=root,
                difficulty=3,
                solution_hint="Найди дискриминант и используй формулу корней квадратного уравнения.",
            )
        )
        idx += 1

    # степени и корни
    pow_cases = [(2, 3), (5, 2), (10, 2), (3, 4)]
    for base, p in pow_cases:
        text = f"Вычисли: {base}^{p}."
        tasks.append(
            TaskDef(
                id=make_id(8, idx),
                grade=8,
                topic="степени и корни",
                text=text,
                answer_type="numeric",
                correct_answer=base**p,
                difficulty=2,
                solution_hint="Перемножь основание само на себя нужное количество раз.",
            )
        )
        idx += 1

    root_cases = [4, 9, 16, 25, 36]
    for v in root_cases:
        text = f"Найди значение выражения: √{v}."
        tasks.append(
            TaskDef(
                id=make_id(8, idx),
                grade=8,
                topic="степени и корни",
                text=text,
                answer_type="numeric",
                correct_answer=int(v**0.5),
                difficulty=1,
                solution_hint="Подумай, какое число в квадрате даёт это значение.",
            )
        )
        idx += 1

    # простая геометрия: площадь прямоугольника
    rects = [(3, 7), (4, 9), (5, 6), (8, 2)]
    for a, b in rects:
        text = f"Найди площадь прямоугольника со сторонами {a} см и {b} см."
        tasks.append(
            TaskDef(
                id=make_id(8, idx),
                grade=8,
                topic="геометрия",
                text=text,
                answer_type="numeric",
                correct_answer=a * b,
                difficulty=1,
                solution_hint="Площадь прямоугольника равна произведению его сторон.",
            )
        )
        idx += 1

    def topic_count(name: str) -> int:
        return sum(1 for t in tasks if t.topic == name)

    # квадратные уравнения
    while topic_count("квадратные уравнения") < 500:
        # a x^2 + b x + c = 0 с целыми корнями
        r1 = -5 + (idx * 2) % 11
        r2 = -5 + (idx * 3) % 11
        a = 1
        b = -(r1 + r2)
        c = r1 * r2
        text = f"Реши уравнение: {a}x² + {b}x + {c} = 0. Введи один из корней."
        tasks.append(
            TaskDef(
                id=make_id(8, idx),
                grade=8,
                topic="квадратные уравнения",
                text=text,
                answer_type="numeric",
                correct_answer=r1,
                difficulty=3,
                solution_hint="Вырази коэффициенты через корни или найди дискриминант и реши по формуле.",
            )
        )
        idx += 1

    # степени и корни
    while topic_count("степени и корни") < 500:
        base = 2 + (idx % 9)
        p = 2 + (idx % 4)
        if idx % 3 == 0:
            text = f"Вычисли: {base}^{p}."
            correct = base**p
            hint = "Перемножь основание само на себя нужное количество раз."
        else:
            n = (base * base)
            text = f"Найди значение выражения: √{n}."
            correct = int(n**0.5)
            hint = "Подумай, какое число в квадрате даёт это значение."
        tasks.append(
            TaskDef(
                id=make_id(8, idx),
                grade=8,
                topic="степени и корни",
                text=text,
                answer_type="numeric",
                correct_answer=correct,
                difficulty=2,
                solution_hint=hint,
            )
        )
        idx += 1

    # геометрия
    while topic_count("геометрия") < 500:
        a = 2 + (idx * 2) % 20
        b = 3 + (idx * 3) % 20
        text = f"Найди площадь прямоугольника со сторонами {a} см и {b} см."
        tasks.append(
            TaskDef(
                id=make_id(8, idx),
                grade=8,
                topic="геометрия",
                text=text,
                answer_type="numeric",
                correct_answer=a * b,
                difficulty=1,
                solution_hint="Площадь прямоугольника равна произведению его сторон.",
            )
        )
        idx += 1

    return tasks


def generate_grade9() -> List[TaskDef]:
    tasks: List[TaskDef] = []
    idx = 1

    # линейные уравнения с параметрами попроще
    eq_cases = [(2, -4, 10), (5, 3, 23), (-3, 6, -9)]
    for a, b, c in eq_cases:
        x = (c - b) / a
        text = f"Реши уравнение: {a}x + {b} = {c}. Введи значение x."
        tasks.append(
            TaskDef(
                id=make_id(9, idx),
                grade=9,
                topic="линейные уравнения",
                text=text,
                answer_type="numeric",
                correct_answer=x,
                difficulty=2,
                solution_hint="Перенеси свободный член и раздели на коэффициент при x.",
            )
        )
        idx += 1

    # квадратные уравнения
    cases = [(1, -6, 9), (1, -1, -12), (1, 5, 6)]
    for a, b, c in cases:
        if (a, b, c) == (1, -6, 9):
            root = 3
        elif (a, b, c) == (1, -1, -12):
            root = 4
        else:
            root = -2
        text = f"Реши уравнение: {a}x² + {b}x + {c} = 0. Введи один из корней."
        tasks.append(
            TaskDef(
                id=make_id(9, idx),
                grade=9,
                topic="квадратные уравнения",
                text=text,
                answer_type="numeric",
                correct_answer=root,
                difficulty=3,
                solution_hint="Найди дискриминант и вычисли корни по формуле.",
            )
        )
        idx += 1

    # геометрия: теорема Пифагора
    triples = [(3, 4, 5), (5, 12, 13), (8, 15, 17)]
    for cat1, cat2, hyp in triples:
        text = f"Катеты прямоугольного треугольника равны {cat1} см и {cat2} см. Найди гипотенузу."
        tasks.append(
            TaskDef(
                id=make_id(9, idx),
                grade=9,
                topic="геометрия",
                text=text,
                answer_type="numeric",
                correct_answer=hyp,
                difficulty=2,
                solution_hint="Используй теорему Пифагора: c² = a² + b².",
            )
        )
        idx += 1

    def topic_count(name: str) -> int:
        return sum(1 for t in tasks if t.topic == name)

    # линейные уравнения
    while topic_count("линейные уравнения") < 500:
        a = 2 + (idx * 2) % 20
        b = -20 + (idx * 3) % 41
        x_val = -10 + (idx * 5) % 41
        c = a * x_val + b
        text = f"Реши уравнение: {a}x + {b} = {c}. Введи значение x."
        tasks.append(
            TaskDef(
                id=make_id(9, idx),
                grade=9,
                topic="линейные уравнения",
                text=text,
                answer_type="numeric",
                correct_answer=x_val,
                difficulty=2,
                solution_hint="Перенеси свободный член и раздели на коэффициент при x.",
            )
        )
        idx += 1

    # квадратные уравнения
    while topic_count("квадратные уравнения") < 500:
        r1 = -10 + (idx * 2) % 21
        r2 = -10 + (idx * 3) % 21
        a = 1
        b = -(r1 + r2)
        c = r1 * r2
        text = f"Реши уравнение: {a}x² + {b}x + {c} = 0. Введи один из корней."
        tasks.append(
            TaskDef(
                id=make_id(9, idx),
                grade=9,
                topic="квадратные уравнения",
                text=text,
                answer_type="numeric",
                correct_answer=r1,
                difficulty=3,
                solution_hint="Найди дискриминант и вычисли корни по формуле.",
            )
        )
        idx += 1

    # геометрия (Пифагор и обратные задачи)
    while topic_count("геометрия") < 500:
        a = 3 + (idx * 2) % 20
        b = 4 + (idx * 3) % 20
        c_val = int(math.sqrt(a * a + b * b))
        text = (
            f"Катеты прямоугольного треугольника равны {a} см и {b} см. "
            "Найди гипотенузу."
        )
        tasks.append(
            TaskDef(
                id=make_id(9, idx),
                grade=9,
                topic="геометрия",
                text=text,
                answer_type="numeric",
                correct_answer=c_val,
                difficulty=2,
                solution_hint="Используй теорему Пифагора: c² = a² + b².",
            )
        )
        idx += 1

    return tasks


def write_tasks(grade: int, tasks: List[TaskDef]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"tasks_{grade}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump([asdict(t) for t in tasks], f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(tasks)} tasks to {path}")


def main() -> None:
    write_tasks(5, generate_grade5())
    write_tasks(6, generate_grade6())
    write_tasks(7, generate_grade7())
    write_tasks(8, generate_grade8())
    write_tasks(9, generate_grade9())


if __name__ == "__main__":
    main()

