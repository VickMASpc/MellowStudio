"""Regression: the prior launcher silently accepted 6.12 on a 6.10.2 project."""
from scripts import check_qt_windows as health


def versions(value="6.10.2"):
    return {name: value for name in health.QT_PACKAGES}


def test_python314_compatible_pin_is_explicit():
    assert health.REQUIRED_QT_VERSION == "6.10.2"
    assert not health.mismatched_packages(versions())


def test_installed_612_is_not_considered_healthy():
    assert health.mismatched_packages(versions("6.12.0")) == versions("6.12.0")


def test_missing_and_partial_binding_mismatch():
    current = versions()
    current["shiboken6"] = None
    current["PySide6_Essentials"] = "6.12.0"
    assert health.mismatched_packages(current) == {
        "PySide6_Essentials": "6.12.0",
        "shiboken6": None,
    }


def test_health_check_rejects_version_drift_before_native_import(monkeypatch):
    monkeypatch.setattr(health, "current_versions", lambda: versions("6.12.0"))
    monkeypatch.setattr(
        health,
        "check_qt_native",
        lambda: (_ for _ in ()).throw(AssertionError("unexpected native import")),
    )
    assert health.main(["--quiet"]) == 2
    assert health.main(["--versions-only", "--quiet"]) == 2


def test_health_check_tests_real_native_import_when_versions_match(monkeypatch):
    monkeypatch.setattr(health, "current_versions", lambda: versions())
    monkeypatch.setattr(health, "check_qt_native", lambda: False)
    assert health.main(["--quiet"]) == 1
    assert health.main(["--versions-only", "--quiet"]) == 0
    monkeypatch.setattr(health, "check_qt_native", lambda: True)
    assert health.main(["--quiet"]) == 0
