from __future__ import annotations

import math
import re
from fractions import Fraction
from typing import Iterable, List, Tuple

from .tasks_loader import Task


def _parse_mixed_fraction(value: str) -> Fraction:
    """Парсит строки вида '3 1/4', '1/2', '5' в Fraction."""
    value = value.strip()
    if " " in value:
        whole_str, frac_str = value.split(None, 1)
        whole = int(whole_str)
        frac = _parse_mixed_fraction(frac_str)
        return Fraction(whole) + frac
    if "/" in value:
        num_str, den_str = value.split("/", 1)
        return Fraction(int(num_str), int(den_str))
    # целое или десятичное
    if re.search(r"[.,]", value):
        value = value.replace(",", ".")
        return Fraction.from_float(float(value))
    return Fraction(int(value))


def _to_number(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(_parse_mixed_fraction(value))
    raise ValueError(f"Unsupported numeric value: {value!r}")


def check_numeric(user_input: str, correct_answer, eps: float = 1e-6) -> Tuple[bool, str]:
    try:
        user_num = _to_number(user_input.strip())
    except Exception:
        return False, "Ответ должен быть числом (целым, десятичным или простой дробью)."

    try:
        correct_num = _to_number(correct_answer)
    except Exception:
        return False, "Внутренняя ошибка: неверно задан правильный ответ."

    if math.isfinite(user_num) and math.isfinite(correct_num):
        if abs(user_num - correct_num) <= eps:
            return True, "Верно!"
        return False, "Неверно, проверь вычисления."
    return False, "Неверно."


def _normalize_text(value: str) -> str:
    value = value.strip().lower()
    value = value.replace("ё", "е")
    value = re.sub(r"\s+", " ", value)
    return value


def check_text(user_input: str, correct_answer: str) -> Tuple[bool, str]:
    if _normalize_text(user_input) == _normalize_text(str(correct_answer)):
        return True, "Верно!"
    return False, "Неверно, попробуй ещё раз."


def check_multiple_choice(user_indices: Iterable[int], correct_indices: Iterable[int]) -> Tuple[bool, str]:
    user_set = set(user_indices)
    correct_set = set(correct_indices)
    if not user_set:
        return False, "Нужно выбрать хотя бы один вариант."
    if user_set == correct_set:
        return True, "Верно!"
    return False, "Неверно, проверь выбранные варианты."


def check_task_answer(task: Task, user_input) -> Tuple[bool, str]:
    """Проверяет ответ на задачу, исходя из её типа."""
    if task.answer_type == "numeric":
        text = str(task.text)
        # Для задач на сокращение дроби требуем несократимый вид
        if "Сократи дробь" in text:
            raw_input = str(user_input).strip()
            try:
                user_frac = _parse_mixed_fraction(raw_input)
                correct_frac = _parse_mixed_fraction(str(task.correct_answer))
            except Exception:
                return False, "Ответ должен быть дробью вида a/b или смешанным числом."

            if user_frac != correct_frac:
                return False, "Неверно, попробуй ещё раз."

            # если введена простая дробь a/b, проверяем, что она несократима
            m = re.fullmatch(r"(-?\d+)\s*/\s*(-?\d+)", raw_input)
            if m:
                num = int(m.group(1))
                den = int(m.group(2))
                if math.gcd(num, den) != 1:
                    return False, "Нужно сократить дробь до несократимого вида."

            return True, "Верно!"

        return check_numeric(str(user_input), task.correct_answer)
    if task.answer_type == "text":
        return check_text(str(user_input), str(task.correct_answer))
    if task.answer_type == "multiple_choice":
        if not isinstance(user_input, (list, tuple)):
            return False, "Внутренняя ошибка: ожидается список индексов вариантов."
        if not isinstance(task.correct_answer, (list, tuple)):
            return False, "Внутренняя ошибка: неверно настроен правильный ответ."
        return check_multiple_choice(
            [int(i) for i in user_input],
            [int(i) for i in task.correct_answer],
        )
    return False, "Неизвестный тип ответа."

