from pathlib import Path

from weld_agent import __version__


def test_package_version_is_explicit() -> None:
    assert __version__ == "0.1.0"


def test_readme_documents_terminal_marker_identification() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "identify_weld_markers.ps1" in readme
    assert "marker-input-manifest.json" in readme
    assert "不需要打开 OCC GUI" in readme
