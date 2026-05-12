from pathlib import Path
from uuid import uuid4

import pytest


@pytest.fixture
def tmp_path(request):
    """Workspace-local tmp_path replacement for Windows-restricted temp dirs."""
    root = Path(__file__).parent.parent / ".test_tmp_files"
    root.mkdir(exist_ok=True)
    path = root / f"{request.node.name}_{uuid4().hex}"
    path.mkdir(exist_ok=True)
    return path
