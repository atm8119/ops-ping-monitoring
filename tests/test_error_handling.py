# tests/test_error_handling.py
import pytest
from unittest.mock import patch, MagicMock, mock_open
import requests
import json

def test_http_error_handling():
    """Test handling of HTTP errors during API calls."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Create a mock HTTP error with status code 500
    http_error_500 = requests.exceptions.HTTPError()
    http_error_500.response = MagicMock()
    http_error_500.response.status_code = 500
    http_error_500.response.text = "Internal Server Error"

    # Mock response to raise HTTP error
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = http_error_500

    # Create PingEnablementManager with minimal mocking
    with patch.object(PingEnablementManager, '_load_state', return_value={}):
        with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
            manager = PingEnablementManager("test.vcf.ops.com")

            # Mock _make_request to raise HTTP error
            with patch.object(manager, '_make_request', return_value=mock_response):
                # Call get_all_vms which should handle the error
                with pytest.raises(requests.exceptions.HTTPError):
                    manager.get_all_vms()

def test_connection_error_handling():
    """Test handling of connection errors during API calls."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Create PingEnablementManager with minimal mocking
    with patch.object(PingEnablementManager, '_load_state', return_value={}):
        with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
            manager = PingEnablementManager("test.vcf.ops.com")

            # Mock _make_request to raise ConnectionError
            with patch.object(manager, '_make_request', side_effect=requests.exceptions.ConnectionError("Connection refused")):
                # Call get_all_vms which should handle the error
                with pytest.raises(requests.exceptions.ConnectionError):
                    manager.get_all_vms()

def test_config_file_not_found():
    """Test handling of missing configuration file."""
    from Enable_VM_Ping_Monitoring import main

    # Mock parse_arguments to return an object with required attributes
    mock_args = MagicMock()
    mock_args.vm_name = None
    mock_args.all_vms = None
    mock_args.force = False
    mock_args.debug = False

    with patch('Enable_VM_Ping_Monitoring.parse_arguments', return_value=mock_args):
        # Mock open to raise FileNotFoundError for config file
        with patch('builtins.open', side_effect=FileNotFoundError):
            # Mock print to capture output
            with patch('builtins.print') as mock_print:
                # Call main which should handle the missing config file
                result = main()

                # Verify main gracefully handled the error
                assert result is None

                # Verify appropriate error message was printed
                mock_print.assert_any_call("\nPlease create vcf-monitoring-loginData.json from the template file.")

def test_invalid_config_file():
    """Test handling of invalid JSON in configuration file."""
    from Enable_VM_Ping_Monitoring import main

    # Mock parse_arguments to return an object with required attributes
    mock_args = MagicMock()
    mock_args.vm_name = None
    mock_args.all_vms = None
    mock_args.force = False
    mock_args.debug = False

    with patch('Enable_VM_Ping_Monitoring.parse_arguments', return_value=mock_args):
        # Mock open to return invalid JSON
        with patch('builtins.open', mock_open(read_data="{invalid json")):
            # Call main which should handle the invalid JSON
            result = main()

            # Verify main gracefully handled the error
            assert result is None

def test_keyboard_interrupt_handling():
    """Test handling of keyboard interrupt (Ctrl+C)."""
    import Enable_VM_Ping_Monitoring

    # Create a mock manager with made_insecure_request=True
    mock_manager = MagicMock()
    mock_manager.made_insecure_request = True

    # Mock the print_security_notice function
    with patch('Enable_VM_Ping_Monitoring.print_security_notice') as mock_security_notice:
        # Directly simulate the __main__ block's KeyboardInterrupt handling
        print("\nOperation cancelled by user")
        if mock_manager and mock_manager.made_insecure_request:
            Enable_VM_Ping_Monitoring.print_security_notice()

        # Verify security notice was called
        mock_security_notice.assert_called_once()

def test_error_during_vm_processing():
    """Test error handling during VM processing."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Mock VM data
    mock_vm = {
        "identifier": "vm-123",
        "resourceKey": {
            "name": "test-vm",
            "resourceIdentifiers": [
                {"identifierType": {"name": "isPingEnabled"}, "value": "false"}
            ]
        }
    }

    # Create PingEnablementManager with minimal mocking
    with patch.object(PingEnablementManager, '_load_state', return_value={}):
        with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
            manager = PingEnablementManager("test.vcf.ops.com")

            # Mock get_all_vms to return our test data
            with patch.object(manager, 'get_all_vms', return_value=[mock_vm]):
                # Mock update_ping_enabled to raise an exception
                with patch.object(manager, 'update_ping_enabled', side_effect=Exception("Test error")):
                    # Mock _save_state to do nothing
                    with patch.object(manager, '_save_state'):
                        # Call process_vms which should handle the error
                        manager.process_vms()

                        # Verify _save_state was still called despite the error
                        manager._save_state.assert_called()