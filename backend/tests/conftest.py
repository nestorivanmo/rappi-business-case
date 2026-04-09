import os
import pytest

from app.engine import DiagnosticEngine


@pytest.fixture(scope="session")
def engine():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "dataset.csv")
    return DiagnosticEngine(data_path=data_path, health_threshold=60.0)


@pytest.fixture(scope="session")
def df(engine):
    return engine.df
