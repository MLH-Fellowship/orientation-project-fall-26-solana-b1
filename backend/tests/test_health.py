from app.routes.health import health_check


def test_health_check():
    assert health_check() == {"status": "ok"}
