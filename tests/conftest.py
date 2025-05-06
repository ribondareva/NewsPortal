import logging

import pytest
from django.db import connection

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def show_db_name():
    # Проверка, что используется именно временная база данных, а не продовая
    logger.info(f"DB in use: {connection.settings_dict['NAME']}")
