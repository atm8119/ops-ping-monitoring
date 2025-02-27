# tests/test_cli.py
import pytest
from unittest.mock import patch, MagicMock, mock_open
import argparse

def test_parse_arguments_vm_name():
    """Test parsing command-line arguments with vm-name."""
    from Enable_VM_Ping_Monitoring import parse_arguments

    # Mock sys.argv
    with patch('sys.argv', ['Enable_VM_Ping_Monitoring.py', '--vm-name', 'test-vm-1', 'test-vm-2']):
        args = parse_arguments()

        # Verify arguments
        assert args.vm_name == ['test-vm-1', 'test-vm-2']
        assert not args.all_vms
        assert not args.force
        assert not args.debug

def test_parse_arguments_all_vms():
    """Test parsing command-line arguments with all-vms."""
    from Enable_VM_Ping_Monitoring import parse_arguments

    # Mock sys.argv
    with patch('sys.argv', ['Enable_VM_Ping_Monitoring.py', '--all-vms']):
        args = parse_arguments()

        # Verify arguments
        assert args.all_vms
        assert not args.vm_name
        assert not args.force
        assert not args.debug

def test_parse_arguments_force():
    """Test parsing command-line arguments with force."""
    from Enable_VM_Ping_Monitoring import parse_arguments

    # Mock sys.argv
    with patch('sys.argv', ['Enable_VM_Ping_Monitoring.py', '--vm-name', 'test-vm', '--force']):
        args = parse_arguments()

        # Verify arguments
        assert args.vm_name == ['test-vm']
        assert args.force
        assert not args.debug

def test_parse_arguments_debug():
    """Test parsing command-line arguments with debug."""
    from Enable_VM_Ping_Monitoring import parse_arguments

    # Mock sys.argv
    with patch('sys.argv', ['Enable_VM_Ping_Monitoring.py', '--all-vms', '--debug']):
        args = parse_arguments()

        # Verify arguments
        assert args.all_vms
        assert args.debug
        assert not args.force

def test_main_cli_mode_vm_name():
    """Test main function in CLI mode with vm-name."""
    from Enable_VM_Ping_Monitoring import main

    # Mock argparse.ArgumentParser to return specific args
    mock_args = MagicMock()
    mock_args.vm_name = ['test-vm']
    mock_args.all_vms = False
    mock_args.force = False
    mock_args.debug = False

    with patch('Enable_VM_Ping_Monitoring.parse_arguments', return_value=mock_args):
        # Mock config loading
        mock_config = '{"operationsHost":"test.vcf.ops.com"}'
        with patch('builtins.open', mock_open(read_data=mock_config)):
            # Mock PingEnablementManager
            mock_manager = MagicMock()
            with patch('Enable_VM_Ping_Monitoring.PingEnablementManager', return_value=mock_manager):
                main()

                # Verify PingEnablementManager.process_vms was called correctly
                mock_manager.process_vms.assert_called_once_with(vm_names=['test-vm'], force_update=False)

def test_main_cli_mode_all_vms():
    """Test main function in CLI mode with all-vms."""
    from Enable_VM_Ping_Monitoring import main

    # Mock argparse.ArgumentParser to return specific args
    mock_args = MagicMock()
    mock_args.vm_name = None
    mock_args.all_vms = True
    mock_args.force = True
    mock_args.debug = False

    with patch('Enable_VM_Ping_Monitoring.parse_arguments', return_value=mock_args):
        # Mock config loading
        mock_config = '{"operationsHost":"test.vcf.ops.com"}'
        with patch('builtins.open', mock_open(read_data=mock_config)):
            # Mock PingEnablementManager
            mock_manager = MagicMock()
            with patch('Enable_VM_Ping_Monitoring.PingEnablementManager', return_value=mock_manager):
                main()

                # Verify PingEnablementManager.process_vms was called correctly
                mock_manager.process_vms.assert_called_once_with(vm_names=None, force_update=True)
