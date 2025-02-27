# tests/test_ping_enablement.py
import pytest
from unittest.mock import patch, MagicMock
import requests
from datetime import datetime

def test_update_ping_enabled_needed():
    """Test updating isPingEnabled when update is needed."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Mock VM data with isPingEnabled = false
    vm_data = {
        "identifier": "vm-123",
        "resourceKey": {
            "name": "test-vm",
            "resourceIdentifiers": [
                {"identifierType": {"name": "isPingEnabled"}, "value": "false"},
                {"identifierType": {"name": "VMEntityName"}, "value": "test-vm"},
                {"identifierType": {"name": "VMEntityObjectID"}, "value": "123"},
                {"identifierType": {"name": "VMEntityVCID"}, "value": "vc-123"}
            ]
        }
    }

    # Mock response for update request
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    # Create PingEnablementManager with minimal mocking
    with patch.object(PingEnablementManager, '_load_state', return_value={}):
        with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
            with patch.object(PingEnablementManager, '_make_request', return_value=mock_response):
                manager = PingEnablementManager("test.vcf.ops.com")

                # Call the method
                result = manager.update_ping_enabled(vm_data)

                # Verify result
                assert result is True

                # Verify _make_request was called correctly
                manager._make_request.assert_called_once()
                call_args = manager._make_request.call_args[1]
                assert call_args["method"] == "PUT"
                assert call_args["url"] == "https://test.vcf.ops.com/suite-api/api/resources"

                # Verify payload contains isPingEnabled=true
                payload = call_args["json"]
                for identifier in payload["resourceKey"]["resourceIdentifiers"]:
                    if identifier["identifierType"]["name"] == "isPingEnabled":
                        assert identifier["value"] == "true"

                # Verify VM was added to processed_vms
                assert "vm-123" in manager.processed_vms
                assert manager.processed_vms["vm-123"]["name"] == "test-vm"
                assert manager.processed_vms["vm-123"]["action"] == "ping_enabled"

def test_update_ping_enabled_not_needed():
    """Test updating isPingEnabled when no update is needed."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Mock VM data with isPingEnabled = true
    vm_data = {
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

    # Create PingEnablementManager with minimal mocking
    with patch.object(PingEnablementManager, '_load_state', return_value={}):
        with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
            manager = PingEnablementManager("test.vcf.ops.com")

            # Explicitly add a mock for _make_request
            manager._make_request = MagicMock()

            # Call the method
            result = manager.update_ping_enabled(vm_data)

            # Verify result
            assert result is False

            # Verify that _make_request was not called
            assert not manager._make_request.called

def test_update_ping_enabled_cached():
    """Test updating isPingEnabled when VM is already in cache."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Mock VM data
    vm_data = {
        "identifier": "vm-789",
        "resourceKey": {
            "name": "test-vm-3",
            "resourceIdentifiers": [
                {"identifierType": {"name": "isPingEnabled"}, "value": "false"}
            ]
        }
    }

    # Mock cached data
    cached_data = {
        "vm-789": {
            "name": "test-vm-3",
            "first_processed": "2025-01-01T00:00:00.000000",
            "last_processed": "2025-01-01T00:00:00.000000",
            "ops_source": "test.vcf.ops.com",
            "action": "ping_enabled"
        }
    }

    # Create PingEnablementManager with mock cached data
    with patch.object(PingEnablementManager, '_load_state', return_value=cached_data):
        with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
            manager = PingEnablementManager("test.vcf.ops.com")

            # Call the method - should skip due to cache
            result = manager.update_ping_enabled(vm_data, force_update=False)

            # Verify result
            assert result is False

            # Force update should process even if in cache
            with patch.object(manager, '_make_request') as mock_request:
                mock_response = MagicMock()
                mock_response.raise_for_status.return_value = None
                mock_request.return_value = mock_response

                result = manager.update_ping_enabled(vm_data, force_update=True)

                # Verify result with force update
                assert result is True
                assert mock_request.called

def test_process_vms_all():
    """Test processing all VMs."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Mock VMs data
    mock_vms = [
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

    # Create PingEnablementManager with minimal mocking
    with patch.object(PingEnablementManager, '_load_state', return_value={}):
        with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
            manager = PingEnablementManager("test.vcf.ops.com")

            # Mock get_all_vms to return our test data
            with patch.object(manager, 'get_all_vms', return_value=mock_vms):
                # Mock update_ping_enabled to return True for the first VM, False for the second
                with patch.object(manager, 'update_ping_enabled', side_effect=[True, False]):
                    # Mock _save_state to do nothing
                    with patch.object(manager, '_save_state'):
                        # Call process_vms with no specific VMs (all VMs)
                        manager.process_vms()

                        # Verify get_all_vms was called
                        manager.get_all_vms.assert_called_once()

                        # Verify update_ping_enabled was called for each VM
                        assert manager.update_ping_enabled.call_count == 2

                        # Verify _save_state was called at least once
                        manager._save_state.assert_called()

def test_process_vms_specific():
    """Test processing specific VMs."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Mock VMs data
    mock_vms = [
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

    # Create PingEnablementManager with minimal mocking
    with patch.object(PingEnablementManager, '_load_state', return_value={}):
        with patch.object(PingEnablementManager, '_get_bearer_token', return_value="test-token"):
            manager = PingEnablementManager("test.vcf.ops.com")

            # Mock get_specific_vms to return our test data
            with patch.object(manager, 'get_specific_vms', return_value=mock_vms):
                # Mock update_ping_enabled to return True
                with patch.object(manager, 'update_ping_enabled', return_value=True):
                    # Mock _save_state to do nothing
                    with patch.object(manager, '_save_state'):
                        # Call process_vms with specific VMs
                        manager.process_vms(vm_names=["test-vm-1"])

                        # Verify get_specific_vms was called with the right VM name
                        manager.get_specific_vms.assert_called_once_with(["test-vm-1"])

                        # Verify update_ping_enabled was called once
                        manager.update_ping_enabled.assert_called_once()

                        # Verify _save_state was called
                        manager._save_state.assert_called()