from __future__ import annotations

import pytest
from sqlalchemy import create_engine


@pytest.fixture()
def sqlite_engine():
    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()
