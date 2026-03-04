from __future__ import annotations

from pathlib import Path

import pytest

from src.contracts import REQUIRED_AUDIT_COLUMNS, REQUIRED_CORE_COLUMNS, missing_columns


_SKIP_DIR_NAMES = {
    ".git",
    ".pytest_cache",
    ".tmp_pytest",
    "__pycache__",
}


def _iter_text_targets(root: Path):
    patterns = [
        "*.md",
        "*.py",
        "*.ini",
        "*.toml",
        "*.yaml",
        "*.yml",
        "*.json",
        "*.csv",
    ]
    include_roots = [root / "docs", root / "src", root / "tests", root / "data" / "raw"]
    include_files = [root / "README.md", root / "pytest.ini"]
    seen: set[Path] = set()
    for path in include_files:
        if path.exists():
            seen.add(path)
            yield path
    for base in include_roots:
        if not base.exists():
            continue
        for pattern in patterns:
            for path in base.rglob(pattern):
                if path in seen:
                    continue
                seen.add(path)
                if any(part in _SKIP_DIR_NAMES for part in path.parts):
                    continue
                if path.name.startswith("pytest-cache-files-"):
                    continue
                yield path


@pytest.mark.contract
def test_phase1_required_columns_missing_count_zero():
    columns = list(REQUIRED_CORE_COLUMNS) + list(REQUIRED_AUDIT_COLUMNS)
    missing = missing_columns(columns, columns)
    assert len(missing) == 0


@pytest.mark.contract
def test_utf8_text_files_decode_and_have_no_replacement_char():
    root = Path(__file__).resolve().parents[2]
    decode_failures: list[str] = []
    replacement_char_files: list[str] = []

    for path in _iter_text_targets(root):
        try:
            data = path.read_bytes()
            text = data.decode("utf-8")
        except (UnicodeDecodeError, PermissionError, OSError):
            decode_failures.append(str(path))
            continue

        if "\ufffd" in text:
            replacement_char_files.append(str(path))

    assert not decode_failures, f"UTF-8 decode failures: {decode_failures}"
    assert (
        not replacement_char_files
    ), f"U+FFFD found in files: {replacement_char_files}"
