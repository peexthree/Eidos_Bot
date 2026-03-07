import pytest
from unittest.mock import patch, MagicMock

@patch('modules.services.ai_worker.logging')
def test_generate_eidos_response_telemetry(mock_logging):
    from modules.services.ai_worker import generate_eidos_response_worker
    # Setup mock conditions to bypass actual processing logic
    with patch('modules.services.ai_worker.cache_db.check_throttle', return_value=True):
         mock_bot = MagicMock()
         generate_eidos_response_worker(mock_bot, 1234, 5678, 'test_analysis')
         # The logging should still be triggered first
         mock_logging.info.assert_called_with("AI Worker started for UID 5678 (Analysis Type: test_analysis)")
