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
