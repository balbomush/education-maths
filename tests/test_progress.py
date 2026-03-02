import json
from pathlib import Path

from app.core.progress import (
    PROGRESS_PATH,
    get_task_progress,
    get_topic_grade_stats,
    get_topic_stats,
    update_progress,
)
from app.core.tasks_loader import Task, load_tasks


def _fake_task(task_id: str, grade: int, topic: str) -> Task:
    # минимальный объект Task для работы прогресса
    return Task(
        id=task_id,
        grade=grade,
        topic=topic,
        text="",
        answer_type="numeric",
        correct_answer=0,
        difficulty=1,
        solution_hint=None,
        options=None,
    )


def test_update_and_get_task_progress(tmp_path, monkeypatch=None):
    """
    Проверяем, что update_progress накапливает попытки и правильные ответы.

    Если pytest доступен, можно воспользоваться monkeypatch и временным файлом.
    В противном случае тест работает с реальным PROGRESS_PATH.
    """
    backup = None
    if PROGRESS_PATH.exists():
        backup = PROGRESS_PATH.read_text(encoding="utf-8")

    try:
        if PROGRESS_PATH.exists():
            PROGRESS_PATH.unlink()

        task = _fake_task("test_task_1", 5, "тестовая тема")
        update_progress(task, is_correct=False)
        update_progress(task, is_correct=True)

        tp = get_task_progress(task)
        assert tp.attempts == 2
        assert tp.correct_attempts == 1
    finally:
        if backup is not None:
            PROGRESS_PATH.write_text(backup, encoding="utf-8")
        elif PROGRESS_PATH.exists():
            PROGRESS_PATH.unlink()


def test_topic_stats_and_grade_stats():
    """
    Проверяем, что агрегирующие функции не падают и выдают осмысленные данные.
    """
    all_tasks = load_tasks()
    assert all_tasks, "Ожидались задачи в банке"

    # имитируем несколько попыток по первым трём задачам
    for t in all_tasks[:3]:
        update_progress(t, is_correct=True)
        update_progress(t, is_correct=False)

    topic_stats = get_topic_stats(all_tasks)
    assert topic_stats, "Ожидалась хотя бы одна тема в статистике"
    for topic, tp in topic_stats.items():
        assert tp.attempts >= tp.correct_attempts

    grade_stats = get_topic_grade_stats(all_tasks)
    assert grade_stats, "Ожидалась статистика по (класс, тема)"
    for (grade, topic), tp in grade_stats.items():
        assert isinstance(grade, int)
        assert isinstance(topic, str)
        assert tp.attempts >= tp.correct_attempts

