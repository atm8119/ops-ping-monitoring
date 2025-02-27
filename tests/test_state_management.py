# tests/test_state_management.py
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime

def test_load_state_empty():
    """Test loading state when file doesn't exist."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Mock file not found
    with patch('builtins.open', side_effect=FileNotFoundError):
        with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
            manager = PingEnablementManager("test.vcf.ops.com")
            assert manager.processed_vms == {}

def test_load_state_invalid_json():
    """Test loading state with invalid JSON."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Mock invalid JSON
    with patch('builtins.open', mock_open(read_data="{")):
        with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
            manager = PingEnablementManager("test.vcf.ops.com")
            assert manager.processed_vms == {}

def test_load_state_valid():
    """Test loading state with valid JSON."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Mock valid JSON
    mock_state = """{
        "vm-123": {
            "name": "test-vm",
            "first_processed": "2025-01-01T00:00:00.000000",
            "last_processed": "2025-01-01T00:00:00.000000",
            "ops_source": "test.vcf.ops.com",
            "action": "ping_enabled"
        }
    }"""

    with patch('builtins.open', mock_open(read_data=mock_state)):
        with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
            manager = PingEnablementManager("test.vcf.ops.com")
            assert "vm-123" in manager.processed_vms
            assert manager.processed_vms["vm-123"]["name"] == "test-vm"

def test_save_state():
    """Test saving state to file."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager
    import json

    # Create a more sophisticated mock for open
    mock_file = MagicMock()
    mock_open_func = mock_open()
    mock_open_func.return_value = mock_file

    with patch('builtins.open', mock_open_func):
        with patch('json.dump') as mock_json_dump:
            with patch.object(PingEnablementManager, '_load_state', return_value={}):
                with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
                    manager = PingEnablementManager("test.vcf.ops.com")

                    # Add a VM to the state
                    manager.processed_vms["vm-456"] = {
                        "name": "new-vm",
                        "first_processed": "2025-02-01T00:00:00.000000",
                        "last_processed": "2025-02-01T00:00:00.000000",
                        "ops_source": "test.vcf.ops.com",
                        "action": "ping_enabled"
                    }

                    # Save the state
                    manager._save_state()

                    # Check that the file was opened for writing
                    mock_open_func.assert_called_with('ping_enabled_vms.json', 'w')

                    # Verify json.dump was called with the correct data
                    mock_json_dump.assert_called_once()
                    args, kwargs = mock_json_dump.call_args
                    assert "vm-456" in args[0]
                    assert args[0]["vm-456"]["name"] == "new-vm"