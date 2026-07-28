"""
Root conftest — pytest fixtures shared across all test modules.
"""

import pytest


@pytest.fixture(scope="session")
def project_root():
    """Absolute path to the project root directory."""
    from pathlib import Path
    return Path(__file__).parent
