from __future__ import annotations

import sys
from pathlib import Path
import shutil
import uuid

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def test_work_dir() -> Path:
    base = ROOT / "data" / "_test_tmp" / uuid.uuid4().hex
    base.mkdir(parents=True, exist_ok=True)
    try:
        yield base
    finally:
        shutil.rmtree(base, ignore_errors=True)
