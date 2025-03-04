# tests/test_integration.py
import pytest
from unittest.mock import patch, MagicMock, mock_open
import requests
import os
import json

# These tests require a more extensive setup and test the integration points
# between different components of the application

@pytest.fixture
def setup_test_files():
    """Setup test files needed for integration tests."""
    # Create temporary files for testing
    test_token = "test-integration-token-123456"
    test_config = {
        "operationsHost": "test-integration.vcf.ops.com",
        "loginData": {
            "username": "test@example.com",
            "authSource": "vIDMAuthSource",
            "password": "TestIntegrationPassword"
        }
    }

    # Write test token file
    with open('test-token.txt', 'w') as f:
        f.write(test_token)

    # Write test config file
    with open('test-config.json', 'w') as f:
        json.dump(test_config, f)

    # Return file paths for cleanup
    yield {
        'token_file': 'test-token.txt',
        'config_file': 'test-config.json'
    }

    # Cleanup after tests
    for file_path in ['test-token.txt', 'test-config.json']:
        if os.path.exists(file_path):
            os.remove(file_path)

def test_token_fetch_integration(setup_test_files):
    """Test the integration between token fetching and the main script."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager
    import Fetch_New_Bearer_Token_VCF_Ops

    # Mock the requests.post to simulate token fetch
    with patch('requests.post') as mock_post:
        # Create a mock response for the token API call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "new-integration-token-987654"
        }
        mock_post.return_value = mock_response

        # Use a dictionary to track which files have been opened
        opened_files = {}

        # Create a custom side effect that doesn't cause recursion
        def custom_open_side_effect(file, mode, *args, **kwargs):
            if file == 'vcf-monitoring-loginData.json':
                # Use the test config file
                return open(setup_test_files['config_file'], mode, *args, **kwargs)
            elif file == 'vcf-monitoring-accessToken.txt':
                # The first time this is called, raise FileNotFoundError
                if file not in opened_files:
                    opened_files[file] = True
                    raise FileNotFoundError
                # Next time, return a file-like object with the token
                return mock_open(read_data="new-integration-token-987654")()
            else:
                # For other files, use the actual open
                return open(file, mode, *args, **kwargs)

        # Patch open with our custom side effect
        with patch('builtins.open', side_effect=custom_open_side_effect):
            # Patch os.getcwd to return the current directory
            with patch('os.getcwd', return_value=os.getcwd()):
                # Remove token file if it exists
                token_file = 'vcf-monitoring-accessToken.txt'
                if os.path.exists(token_file):
                    os.remove(token_file)

                # Mock Fetch_New_Bearer_Token to create a token file
                def mock_fetch_token():
                    with open(token_file, 'w') as f:
                        f.write("new-integration-token-987654")

                with patch.object(Fetch_New_Bearer_Token_VCF_Ops, 'Fetch_New_Bearer_Token', 
                                side_effect=mock_fetch_token):
                    # Create PingEnablementManager with minimal mocking
                    with patch.object(PingEnablementManager, '_load_state', return_value={}):
                        manager = PingEnablementManager("test-integration.vcf.ops.com")

                        # Verify token was fetched
                        Fetch_New_Bearer_Token_VCF_Ops.Fetch_New_Bearer_Token.assert_called_once()

                        # Verify token was loaded
                        assert manager.bearer_token == "new-integration-token-987654"

def test_full_workflow_integration():
    """Test the full workflow from args parsing to VM processing."""
    from Enable_VM_Ping_Monitoring import main
    import scheduler

    # Mock scheduler module to avoid starting real scheduled jobs
    with patch.dict('sys.modules', {'scheduler': MagicMock()}):
        # Mock the scheduler MonitoringScheduler class
        mock_scheduler_class = MagicMock()
        mock_scheduler_instance = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler_instance
        
        # Replace the imported scheduler's MonitoringScheduler with our mock
        scheduler.MonitoringScheduler = mock_scheduler_class

        # Mock command line arguments
        with patch('sys.argv', ['Enable_VM_Ping_Monitoring.py', '--vm-name', 'test-vm-1', '--force']):
            # Mock config file
            mock_config = '{"operationsHost":"test-integration.vcf.ops.com"}'

            with patch('builtins.open', mock_open(read_data=mock_config)):
                # Mock PingEnablementManager methods
                with patch('Enable_VM_Ping_Monitoring.PingEnablementManager') as MockManager:
                    # Create a mock instance that will be returned by the constructor
                    mock_instance = MagicMock()
                    MockManager.return_value = mock_instance

                    # Call main
                    main()

                    # Verify manager was initialized with correct FQDN
                    MockManager.assert_called_once_with("test-integration.vcf.ops.com")

                    # Verify process_vms was called with correct arguments
                    mock_instance.process_vms.assert_called_once_with(vm_names=['test-vm-1'], force_update=True)

                    # Verify scheduler was not actually used
                    assert not mock_scheduler_instance.start.called
                    assert not mock_scheduler_instance.stop.called

def test_scheduler_command_integration():
    """Test integration with the schedule command."""
    from Enable_VM_Ping_Monitoring import main

    # Create a mock scheduler module
    mock_scheduler_module = MagicMock()
    mock_scheduler_instance = MagicMock()
    mock_scheduler_module.MonitoringScheduler.return_value = mock_scheduler_instance

    # Mock the sys.modules to replace scheduler with our mock
    with patch.dict('sys.modules', {'scheduler': mock_scheduler_module}):
        # Mock command line arguments for schedule start
        with patch('sys.argv', ['Enable_VM_Ping_Monitoring.py', 'schedule', 'start']):
            # Mock config file (needed if code attempts to load config)
            mock_config = '{"operationsHost":"test-integration.vcf.ops.com"}'
            with patch('builtins.open', mock_open(read_data=mock_config)):
                # Call main
                main()

                # Verify scheduler start was called
                mock_scheduler_instance.start.assert_called_once()
                assert not mock_scheduler_instance.stop.called

        # Reset the mock for next test
        mock_scheduler_instance.reset_mock()

        # Mock command line arguments for schedule stop
        with patch('sys.argv', ['Enable_VM_Ping_Monitoring.py', 'schedule', 'stop']):
            # Mock config file
            with patch('builtins.open', mock_open(read_data=mock_config)):
                # Call main
                main()

                # Verify scheduler stop was called
                mock_scheduler_instance.stop.assert_called_once()
                assert not mock_scheduler_instance.start.called

        # Reset the mock for next test
        mock_scheduler_instance.reset_mock()

        # Mock command line arguments for schedule configure
        with patch('sys.argv', ['Enable_VM_Ping_Monitoring.py', 'schedule', 'configure', 
                                '--daily', '08:30', '--target-all-vms']):
            # Mock config file
            with patch('builtins.open', mock_open(read_data=mock_config)):
                # Mock process_friendly_schedule_options to return valid updates
                mock_updates = {
                    'schedule_type': 'cron',
                    'cron_expression': '30 8 * * *'
                }
                with patch.object(mock_scheduler_module, 'process_friendly_schedule_options', 
                                    return_value=mock_updates):
                    # Call main
                    main()

                    # Verify scheduler configure was called with expected updates
                    mock_scheduler_instance.configure.assert_called_once()
                    # The vm_names=None indicates target-all-vms was used
                    assert 'vm_names' in mock_scheduler_instance.configure.call_args[0][0]
                    assert mock_scheduler_instance.configure.call_args[0][0]['vm_names'] is None

def test_scheduler_run_now_integration():
    """Test integration with the schedule run-now command."""
    from Enable_VM_Ping_Monitoring import main

    # Create a mock scheduler module
    mock_scheduler_module = MagicMock()
    mock_scheduler_instance = MagicMock()
    mock_scheduler_module.MonitoringScheduler.return_value = mock_scheduler_instance

    # Mock the sys.modules to replace scheduler with our mock
    with patch.dict('sys.modules', {'scheduler': mock_scheduler_module}):
        # Mock command line arguments for schedule run-now
        with patch('sys.argv', ['Enable_VM_Ping_Monitoring.py', 'schedule', 'run-now']):
            # Mock config file
            mock_config = '{"operationsHost":"test-integration.vcf.ops.com"}'
            with patch('builtins.open', mock_open(read_data=mock_config)):
                # Call main
                main()

                # Verify scheduler run_now was called
                mock_scheduler_instance.run_now.assert_called_once()

def test_api_token_refresh_integration():
    """Test token refresh during API calls."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager
    import Fetch_New_Bearer_Token_VCF_Ops

    # Create a mock HTTP error with status code 401
    http_error_401 = requests.exceptions.HTTPError()
    http_error_401.response = MagicMock()
    http_error_401.response.status_code = 401

    # Mock responses for API calls
    mock_response_error = MagicMock()
    mock_response_error.raise_for_status.side_effect = http_error_401

    mock_response_success = MagicMock()
    mock_response_success.raise_for_status.return_value = None
    mock_response_success.json.return_value = {"resourceList": []}

    # Mock fetch token function
    with patch.object(Fetch_New_Bearer_Token_VCF_Ops, 'Fetch_New_Bearer_Token'):
        # Create PingEnablementManager with minimal mocking
        with patch.object(PingEnablementManager, '_load_state', return_value={}):
            with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
                manager = PingEnablementManager("test.vcf.ops.com")

                # Mock _make_request to fail first with 401, then succeed after token refresh
                with patch.object(manager, '_make_request', side_effect=[mock_response_error, mock_response_success]):
                    # Call get_all_vms which should handle the 401 and retry
                    vms = manager.get_all_vms()

                    # Verify token was refreshed
                    Fetch_New_Bearer_Token_VCF_Ops.Fetch_New_Bearer_Token.assert_called_once()

                    # Verify _make_request was called twice (initial failure, then success)
                    assert manager._make_request.call_count == 2