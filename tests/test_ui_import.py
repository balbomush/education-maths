def test_can_import_main_window_and_app():
    """
    Простейший smoke-тест: проверяем, что модуль UI импортируется
    и класс App определён (без запуска главного цикла Tkinter).
    """
    from app.ui.main_window import App

    assert App is not None

