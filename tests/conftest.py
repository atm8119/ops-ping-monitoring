import pytest
import os
import json
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_ops_config():
    """Fixture providing a mock operations config."""
    return {
        "operationsHost": "test.vcf.ops.com",
        "loginData": {
            "username": "test@example.com",
            "authSource": "vIDMAuthSource",
            "password": "TestPassword!"
        }
    }

@pytest.fixture
def mock_vm_data():
    """Fixture providing mock VM data for testing."""
    return [
        {
            "identifier": "vm-123",
            "resourceKey": {
                "name": "test-vm-1",
                "resourceIdentifiers": [
                    {"identifierType": {"name": "isPingEnabled"}, "value": "false"},
                    {"identifierType": {"name": "VMEntityName"}, "value": "test-vm-1"},
                    {"identifierType": {"name": "VMEntityObjectID"}, "value": "123"},
                    {"identifierType": {"name": "VMEntityVCID"}, "value": "vc-123"}
                ]
            }
        },
        {
            "identifier": "vm-456",
            "resourceKey": {
                "name": "test-vm-2",
                "resourceIdentifiers": [
                    {"identifierType": {"name": "isPingEnabled"}, "value": "true"},
                    {"identifierType": {"name": "VMEntityName"}, "value": "test-vm-2"},
                    {"identifierType": {"name": "VMEntityObjectID"}, "value": "456"},
                    {"identifierType": {"name": "VMEntityVCID"}, "value": "vc-456"}
                ]
            }
        }
    ]

@pytest.fixture
def mock_ping_enablement_manager():
    """Fixture providing a mocked PingEnablementManager instance."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Create PingEnablementManager with minimal mocking
    with patch.object(PingEnablementManager, '_load_state', return_value={}):
        with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
            manager = PingEnablementManager("test.vcf.ops.com")

            # Add mock methods for testing
            manager._make_request = MagicMock()

            return manager

@pytest.fixture
def temp_files():
    """Fixture to create and clean up temporary files for testing."""
    # Create temporary files
    files = []

    # Create and return file generator function
    def create_file(filename, content):
        with open(filename, 'w') as f:
            f.write(content)
        files.append(filename)
        return filename

    yield create_file

    # Clean up files
    for file in files:
        if os.path.exists(file):
            os.remove(file)


@pytest.fixture
def mock_scheduler():
    """Fixture providing a mocked MonitoringScheduler instance."""
    # Mock the configuration file
    mock_config = {
        "schedule_type": "interval",
        "interval_unit": "days",
        "interval_value": 1,
        "cron_expression": "0 0 * * *",
        "vm_names": None,
        "force_update": False,
        "enabled": False,
        "last_run": None,
        "next_run": None
    }

    # Create a mock for MonitoringScheduler
    mock_sched = MagicMock()
    mock_sched.config = mock_config.copy()
    mock_sched.config_path = 'test-config.json'

    # Create a mock for the scheduler attribute
    mock_sched.scheduler = MagicMock()

    # Configure the start method to actually call add_job and start on the scheduler
    def mock_start(*args, **kwargs):
        mock_sched.scheduler.add_job()
        mock_sched.scheduler.start()
        return True

    # Configure the stop method to actually call shutdown on the scheduler
    def mock_stop(*args, **kwargs):
        mock_sched.scheduler.shutdown()
        return True

    # Attach the mocked methods
    mock_sched.start = mock_start
    mock_sched.stop = mock_stop

    return mock_sched

@pytest.fixture
def mock_scheduler_module():
    """Create a properly mocked scheduler module."""
    mock_scheduler = MagicMock()

    # Mock the DEFAULT_SCHEDULE_CONFIG
    mock_scheduler.DEFAULT_SCHEDULE_CONFIG = {
        "schedule_type": "interval",
        "interval_unit": "days",
        "interval_value": 1,
        "cron_expression": "0 0 * * *",
        "vm_names": None,
        "force_update": False,
        "enabled": False,
        "last_run": None,
        "next_run": None
    }

    # Return the mocked module
    with patch.dict('sys.modules', {'scheduler': mock_scheduler}):
        yield mock_scheduler

@pytest.fixture
def real_scheduler_fixture():
    """Create a fixture with a real MonitoringScheduler but mocked dependencies."""
    # First, patch the modules the scheduler depends on
    with patch.dict('sys.modules', {'apscheduler': MagicMock()}):
        # Now import the scheduler
        import scheduler

        # Save the original method before we replace it
        original_load_config = scheduler.MonitoringScheduler._load_config

        # Create a simple monkeypatch for _load_config that uses the correct default
        def patched_load_config(self):
            """Return a test config without trying to load from disk."""
            config = {
                "schedule_type": "interval",
                "interval_unit": "days", 
                "interval_value": 1,
                "cron_expression": "0 0 * * *",
                "vm_names": None,
                "force_update": False,
                "enabled": False,
                "last_run": None,
                "next_run": None
            }
            return config

        # Apply the patch
        scheduler.MonitoringScheduler._load_config = patched_load_config

        try:
            # Create instance without needing actual dependencies
            sched = scheduler.MonitoringScheduler()
            sched.scheduler = MagicMock()  # Mock the actual scheduler

            yield sched
        finally:
            # Restore original method
            scheduler.MonitoringScheduler._load_config = original_load_config

@pytest.fixture
def mock_token_fetch():
    """Provide a mocked token fetch function."""
    with patch('Fetch_New_Bearer_Token_VCF_Ops.Fetch_New_Bearer_Token') as mock_fetch:
        yield mock_fetch