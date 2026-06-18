import pytest
from unittest.mock import patch
from backend.services.db_client import FallbackDB

@pytest.mark.asyncio
async def test_init_fallback_file_error():
    db = FallbackDB()

    with patch("os.path.exists", return_value=False), \
         patch("builtins.open", side_effect=Exception("Test open error")), \
         patch("backend.services.db_client.logger.error") as mock_logger_error:

        await db._init_fallback_file()

        mock_logger_error.assert_called_once()
        called_args = mock_logger_error.call_args[0][0]
        assert "Failed to initialize fallback file" in called_args
        assert "Test open error" in called_args
