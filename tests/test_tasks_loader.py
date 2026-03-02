from app.core.tasks_loader import (
    DATA_DIR,
    Task,
    get_available_grades,
    get_topics_for_grade,
    load_tasks,
)


def test_load_tasks_by_grade_and_topic():
    tasks_5 = load_tasks(grade=5)
    assert tasks_5, "Ожидались задачи для 5 класса"
    assert all(t.grade == 5 for t in tasks_5)

    topic = tasks_5[0].topic
    topic_tasks = load_tasks(grade=5, topic=topic)
    assert topic_tasks, "Ожидались задачи по выбранной теме"
    assert all(t.topic == topic for t in topic_tasks)


def test_available_grades_and_topics_consistent():
    grades = get_available_grades()
    assert set(grades).issuperset({5, 6, 7, 8, 9})

    for g in grades:
        topics = get_topics_for_grade(g)
        assert topics, f"Для класса {g} должны быть темы"
        tasks = load_tasks(grade=g)
        topics_from_tasks = {t.topic for t in tasks}
        assert set(topics).issubset(topics_from_tasks)

