from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .tasks_loader import Task, DATA_DIR


PROGRESS_PATH = DATA_DIR / "progress.json"


@dataclass
class TaskProgress:
    attempts: int = 0
    correct_attempts: int = 0

    @property
    def success_rate(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.correct_attempts / self.attempts


def _load_raw_progress() -> Dict[str, dict]:
    if not PROGRESS_PATH.exists():
        return {}
    with PROGRESS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_raw_progress(data: Dict[str, dict]) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_progress(task: Task, is_correct: bool) -> None:
    """Обновить прогресс по конкретной задаче."""
    data = _load_raw_progress()
    rec = data.get(task.id, {"attempts": 0, "correct_attempts": 0})
    rec["attempts"] += 1
    if is_correct:
        rec["correct_attempts"] += 1
    data[task.id] = rec
    _save_raw_progress(data)


def get_task_progress(task: Task) -> TaskProgress:
    data = _load_raw_progress()
    rec = data.get(task.id, {"attempts": 0, "correct_attempts": 0})
    return TaskProgress(
        attempts=int(rec.get("attempts", 0)),
        correct_attempts=int(rec.get("correct_attempts", 0)),
    )


def get_topic_stats(tasks: list[Task]) -> Dict[str, TaskProgress]:
    """Подсчёт прогресса по темам на основе решённых задач."""
    data = _load_raw_progress()
    stats: Dict[str, TaskProgress] = {}
    tasks_by_id = {t.id: t for t in tasks}

    for task_id, rec in data.items():
        task = tasks_by_id.get(task_id)
        if not task:
            continue
        topic = task.topic
        tp = stats.get(topic, TaskProgress())
        tp.attempts += int(rec.get("attempts", 0))
        tp.correct_attempts += int(rec.get("correct_attempts", 0))
        stats[topic] = tp

    return stats

