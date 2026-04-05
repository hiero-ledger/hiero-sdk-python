import pytest

from tests.integration.utils import IntegrationTestEnv


@pytest.fixture
def env():
    """Integration test environment with client/operator set up."""
    e = IntegrationTestEnv()
    yield e
    e.close()
