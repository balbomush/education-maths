from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


@dataclass
class Task:
    id: str
    grade: int
    topic: str
    text: str
    answer_type: str
    correct_answer: Any
    difficulty: int
    solution_hint: Optional[str] = None
    options: Optional[list[str]] = None


def _load_tasks_file(path: Path) -> list[Task]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    tasks: list[Task] = []
    for item in raw:
        tasks.append(
            Task(
                id=str(item["id"]),
                grade=int(item["grade"]),
                topic=str(item["topic"]),
                text=str(item["text"]),
                answer_type=str(item["answer_type"]),
                correct_answer=item["correct_answer"],
                difficulty=int(item.get("difficulty", 1)),
                solution_hint=item.get("solution_hint"),
                options=item.get("options"),
            )
        )
    return tasks


def load_tasks(grade: Optional[int] = None, topic: Optional[str] = None) -> list[Task]:
    """Загрузить список задач, отфильтрованный по классу и теме."""
    tasks: list[Task] = []
    if grade is not None:
        paths: Iterable[Path] = [DATA_DIR / f"tasks_{grade}.json"]
    else:
        paths = sorted(DATA_DIR.glob("tasks_*.json"))

    for path in paths:
        tasks.extend(_load_tasks_file(path))

    if topic is not None:
        tasks = [t for t in tasks if t.topic == topic]

    return tasks


def get_available_grades() -> List[int]:
    grades: list[int] = []
    for path in DATA_DIR.glob("tasks_*.json"):
        name = path.stem  # tasks_5
        try:
            _, g = name.split("_", 1)
            grades.append(int(g))
        except ValueError:
            continue
    return sorted(set(grades))


def get_topics_for_grade(grade: int) -> List[str]:
    topics: set[str] = set()
    for task in load_tasks(grade=grade):
        topics.add(task.topic)
    return sorted(topics)

