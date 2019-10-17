from unittest.mock import MagicMock
import pytest

@pytest.fixture()
def local_client():
    mock = MagicMock()
    return mock
