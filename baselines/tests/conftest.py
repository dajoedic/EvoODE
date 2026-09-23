import re
import uuid
from pathlib import Path

import pytest


@pytest.fixture
def tmp_path(request):
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", request.node.name)
    path = Path("outputs") / "wp_n21_pytest_tmp" / f"{name}_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()
