# tests/test_api_calls.py
import pytest
from unittest.mock import patch, MagicMock
import requests

def test_get_all_vms():
    """Test fetching all VMs."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Mock response data
    mock_vm_data = {
        "resourceList": [
            {
                "identifier": "vm-123",
                "resourceKey": {
                    "name": "test-vm-1",
                    "resourceIdentifiers": [
                        {"identifierType": {"name": "isPingEnabled"}, "value": "false"}
                    ]
                }
            },
            {
                "identifier": "vm-456",
                "resourceKey": {
                    "name": "test-vm-2",
                    "resourceIdentifiers": [
                        {"identifierType": {"name": "isPingEnabled"}, "value": "true"}
                    ]
                }
            }
        ]
    }

    # Mock response
    mock_response = MagicMock()
    mock_response.json.return_value = mock_vm_data
    mock_response.raise_for_status.return_value = None

    # Create PingEnablementManager with minimal mocking
    with patch.object(PingEnablementManager, '_load_state', return_value={}):
        with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
            with patch.object(PingEnablementManager, '_make_request', return_value=mock_response):
                manager = PingEnablementManager("test.vcf.ops.com")
                vms = manager.get_all_vms()

                # Verify returned data
                assert len(vms) == 2
                assert vms[0]["identifier"] == "vm-123"
                assert vms[1]["identifier"] == "vm-456"

                # Verify _make_request was called correctly
                manager._make_request.assert_called_once()
                call_args = manager._make_request.call_args[1]
                assert call_args["method"] == "GET"
                assert call_args["url"] == "https://test.vcf.ops.com/suite-api/api/resources"
                assert call_args["params"] == {"resourceKind": "VirtualMachine", "adapterKind": "VMWARE"}

def test_get_specific_vms():
    """Test fetching specific VMs by name."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Mock response data for each VM request
    mock_vm_data_1 = {
        "resourceList": [
            {
                "identifier": "vm-123",
                "resourceKey": {
                    "name": "test-vm-1",
                    "resourceIdentifiers": [
                        {"identifierType": {"name": "isPingEnabled"}, "value": "false"}
                    ]
                }
            }
        ]
    }

    mock_vm_data_2 = {
        "resourceList": [
            {
                "identifier": "vm-456",
                "resourceKey": {
                    "name": "test-vm-2",
                    "resourceIdentifiers": [
                        {"identifierType": {"name": "isPingEnabled"}, "value": "true"}
                    ]
                }
            }
        ]
    }

    # Mock responses
    mock_response_1 = MagicMock()
    mock_response_1.json.return_value = mock_vm_data_1
    mock_response_1.raise_for_status.return_value = None

    mock_response_2 = MagicMock()
    mock_response_2.json.return_value = mock_vm_data_2
    mock_response_2.raise_for_status.return_value = None

    # Create PingEnablementManager with minimal mocking
    with patch.object(PingEnablementManager, '_load_state', return_value={}):
        with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
            with patch.object(PingEnablementManager, '_make_request', side_effect=[mock_response_1, mock_response_2]):
                manager = PingEnablementManager("test.vcf.ops.com")
                vms = manager.get_specific_vms(["test-vm-1", "test-vm-2"])

                # Verify returned data
                assert len(vms) == 2
                assert vms[0]["identifier"] == "vm-123"
                assert vms[1]["identifier"] == "vm-456"

                # Verify _make_request was called correctly
                assert manager._make_request.call_count == 2
                call_args_1 = manager._make_request.call_args_list[0][1]
                assert call_args_1["params"]["name"] == "test-vm-1"
                call_args_2 = manager._make_request.call_args_list[1][1]
                assert call_args_2["params"]["name"] == "test-vm-2"