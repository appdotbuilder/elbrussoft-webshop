def test_ui_modules_import():
    """Test that UI modules can be imported without errors."""
    import app.store
    import app.admin
    import app.startup

    assert app.store is not None
    assert app.admin is not None
    assert app.startup is not None


def test_startup_function_exists():
    """Test that startup function exists and can be called."""
    from app.startup import startup

    # The function should exist and be callable
    assert callable(startup)
