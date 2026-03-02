from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from .tasks_loader import Task


def _get_progress_path() -> Path:
    """
    Возвращает путь к файлу прогресса.

    Для собранного .exe нельзя писать внутрь каталога с ресурсами (_MEIPASS),
    поэтому используем пользовательскую директорию (AppData / HOME).
    В режиме разработки файл лежит рядом с проектом в подкаталоге data/.
    """
    base_dir = Path.cwd()
    # Если приложение запущено из замороженного .exe, кладём прогресс в %APPDATA%
    if getattr(__import__("sys"), "frozen", False):
        appdata = os.getenv("APPDATA")
        if appdata:
            base_dir = Path(appdata) / "education-maths"
    else:
        # режим разработки: хранить в data/progress.json в корне проекта
        project_root = Path(__file__).resolve().parents[2]
        base_dir = project_root / "data"
    return base_dir / "progress.json"


PROGRESS_PATH = _get_progress_path()


@dataclass
class TaskProgress:
    attempts: int = 0
    correct_attempts: int = 0

    @property
    def success_rate(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.correct_attempts / self.attempts


def _ensure_structure(raw: Dict) -> Dict:
    """
    Нормализует структуру файла прогресса.

    Старый формат:
        { "<task_id>": {"attempts": ..., "correct_attempts": ...}, ... }

    Новый формат:
        {
          "tasks": { "<task_id>": {...}, ... },
          "sessions": [ { id, topic, started_at, tasks: {...} }, ... ]
        }
    """
    if "tasks" in raw or "sessions" in raw:
        raw.setdefault("tasks", {})
        raw.setdefault("sessions", [])
        return raw
    # миграция со старого формата
    return {"tasks": raw, "sessions": []}


def _load_raw_progress() -> Dict:
    if not PROGRESS_PATH.exists():
        return {"tasks": {}, "sessions": []}
    with PROGRESS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return _ensure_structure(data)


def _save_raw_progress(data: Dict) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def start_session(topic: str) -> str:
    """
    Создаёт запись о новой сессии и возвращает её идентификатор.
    """
    data = _load_raw_progress()
    sessions: List[Dict] = data.setdefault("sessions", [])
    ts = datetime.now().isoformat(timespec="seconds")
    session_id = f"{ts}"
    session = {
        "id": session_id,
        "topic": topic,
        "started_at": ts,
        "tasks": {},
    }
    sessions.append(session)
    _save_raw_progress(data)
    return session_id


def update_progress(task: Task, is_correct: bool, session_id: str | None = None) -> None:
    """
    Обновить прогресс по конкретной задаче и, при необходимости, в рамках сессии.
    """
    data = _load_raw_progress()
    tasks_data: Dict[str, Dict] = data.setdefault("tasks", {})

    # общий прогресс по задаче
    rec = tasks_data.get(task.id, {"attempts": 0, "correct_attempts": 0})
    rec["attempts"] += 1
    if is_correct:
        rec["correct_attempts"] += 1
    tasks_data[task.id] = rec

    # прогресс внутри конкретной сессии
    if session_id:
        sessions: List[Dict] = data.setdefault("sessions", [])
        session = next((s for s in sessions if s.get("id") == session_id), None)
        if session is None:
            # на всякий случай создадим сессию, если её нет
            session = {
                "id": session_id,
                "topic": task.topic,
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "tasks": {},
            }
            sessions.append(session)
        stasks: Dict[str, Dict] = session.setdefault("tasks", {})
        srec = stasks.get(task.id, {"attempts": 0, "correct_attempts": 0})
        srec["attempts"] += 1
        if is_correct:
            srec["correct_attempts"] += 1
        stasks[task.id] = srec

    _save_raw_progress(data)


def get_task_progress(task: Task) -> TaskProgress:
    data = _load_raw_progress()
    tasks_data: Dict[str, Dict] = data.get("tasks", {})
    rec = tasks_data.get(task.id, {"attempts": 0, "correct_attempts": 0})
    return TaskProgress(
        attempts=int(rec.get("attempts", 0)),
        correct_attempts=int(rec.get("correct_attempts", 0)),
    )


def get_topic_stats(tasks: list[Task]) -> Dict[str, TaskProgress]:
    """Подсчёт прогресса по темам на основе решённых задач."""
    data = _load_raw_progress()
    tasks_data: Dict[str, Dict] = data.get("tasks", {})
    stats: Dict[str, TaskProgress] = {}
    tasks_by_id = {t.id: t for t in tasks}

    for task_id, rec in tasks_data.items():
        task = tasks_by_id.get(task_id)
        if not task:
            continue
        topic = task.topic
        tp = stats.get(topic, TaskProgress())
        tp.attempts += int(rec.get("attempts", 0))
        tp.correct_attempts += int(rec.get("correct_attempts", 0))
        stats[topic] = tp

    return stats


def get_topic_grade_stats(tasks: list[Task]) -> Dict[Tuple[int, str], TaskProgress]:
    """Подсчёт прогресса по темам с учётом класса."""
    data = _load_raw_progress()
    tasks_data: Dict[str, Dict] = data.get("tasks", {})
    stats: Dict[Tuple[int, str], TaskProgress] = {}
    tasks_by_id = {t.id: t for t in tasks}

    for task_id, rec in tasks_data.items():
        task = tasks_by_id.get(task_id)
        if not task:
            continue
        key = (task.grade, task.topic)
        tp = stats.get(key, TaskProgress())
        tp.attempts += int(rec.get("attempts", 0))
        tp.correct_attempts += int(rec.get("correct_attempts", 0))
        stats[key] = tp

    return stats


def get_sessions() -> List[Dict]:
    """Возвращает список всех сессий (для UI и отчётов)."""
    data = _load_raw_progress()
    return list(data.get("sessions", []))


def get_session_task_stats(session_id: str) -> Dict[str, TaskProgress]:
    """Возвращает статистику по задачам внутри конкретной сессии."""
    for session in get_sessions():
        if session.get("id") == session_id:
            stasks: Dict[str, Dict] = session.get("tasks", {})
            result: Dict[str, TaskProgress] = {}
            for task_id, rec in stasks.items():
                result[task_id] = TaskProgress(
                    attempts=int(rec.get("attempts", 0)),
                    correct_attempts=int(rec.get("correct_attempts", 0)),
                )
            return result
    return {}


def get_recent_task_ids_for_topic(topic: str, max_sessions: int = 3) -> set[str]:
    """
    Возвращает множество task_id, которые использовались в последних max_sessions
    сессиях по заданной теме. Используется, чтобы не повторять задачи в новых
    тренировках.
    """
    sessions = [
        s for s in get_sessions() if s.get("topic") == topic and s.get("tasks")
    ]
    # сортируем по времени (новые сначала)
    sessions.sort(key=lambda s: s.get("started_at", ""), reverse=True)
    recent = sessions[:max_sessions]
    result: set[str] = set()
    for s in recent:
        result.update(s.get("tasks", {}).keys())
    return result

