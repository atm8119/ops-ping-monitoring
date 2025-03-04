# tests/test_interactive.py
import pytest
from unittest.mock import patch, MagicMock, mock_open

def test_main_interactive_single_vm():
    """Test main function in interactive mode with single VM."""
    from Enable_VM_Ping_Monitoring import main

    # Mock argparse.ArgumentParser to return empty args (interactive mode)
    mock_args = MagicMock()
    mock_args.vm_name = None
    mock_args.all_vms = None
    mock_args.force = False
    mock_args.debug = False

    with patch('Enable_VM_Ping_Monitoring.parse_arguments', return_value=mock_args):
        # Mock config loading
        mock_config = '{"operationsHost":"test.vcf.ops.com"}'
        with patch('builtins.open', mock_open(read_data=mock_config)):
            # Mock PingEnablementManager
            mock_manager = MagicMock()
            with patch('Enable_VM_Ping_Monitoring.PingEnablementManager', return_value=mock_manager):
                # Mock input responses for interactive mode
                with patch('builtins.input', side_effect=['1', 'test-vm', 'n']):
                    # Mock print to avoid output during test
                    with patch('builtins.print'):
                        main()

                        # Verify PingEnablementManager.process_vms was called correctly
                        mock_manager.process_vms.assert_called_once_with(vm_names=['test-vm'], force_update=False)

def test_main_interactive_multiple_vms():
    """Test main function in interactive mode with multiple VMs."""
    from Enable_VM_Ping_Monitoring import main

    # Mock argparse.ArgumentParser to return empty args (interactive mode)
    mock_args = MagicMock()
    mock_args.vm_name = None
    mock_args.all_vms = None
    mock_args.force = False
    mock_args.debug = False

    with patch('Enable_VM_Ping_Monitoring.parse_arguments', return_value=mock_args):
        # Mock config loading
        mock_config = '{"operationsHost":"test.vcf.ops.com"}'
        with patch('builtins.open', mock_open(read_data=mock_config)):
            # Mock PingEnablementManager
            mock_manager = MagicMock()
            with patch('Enable_VM_Ping_Monitoring.PingEnablementManager', return_value=mock_manager):
                # Mock input responses for interactive mode
                with patch('builtins.input', side_effect=['2', 'test-vm-1', 'test-vm-2', '', 'y']):
                    # Mock print to avoid output during test
                    with patch('builtins.print'):
                        main()

                        # Verify PingEnablementManager.process_vms was called correctly
                        mock_manager.process_vms.assert_called_once_with(vm_names=['test-vm-1', 'test-vm-2'], force_update=True)

def test_main_interactive_all_vms():
    """Test main function in interactive mode with all VMs."""
    from Enable_VM_Ping_Monitoring import main

    # Mock argparse.ArgumentParser to return empty args (interactive mode)
    mock_args = MagicMock()
    mock_args.vm_name = None
    mock_args.all_vms = None
    mock_args.force = False
    mock_args.debug = False

    with patch('Enable_VM_Ping_Monitoring.parse_arguments', return_value=mock_args):
        # Mock config loading
        mock_config = '{"operationsHost":"test.vcf.ops.com"}'
        with patch('builtins.open', mock_open(read_data=mock_config)):
            # Mock PingEnablementManager
            mock_manager = MagicMock()
            with patch('Enable_VM_Ping_Monitoring.PingEnablementManager', return_value=mock_manager):
                # Mock input responses for interactive mode
                with patch('builtins.input', side_effect=['3', '2']):  # Option 3 for ALL VMs, Option 2 for force process
                    # Mock print to avoid output during test
                    with patch('builtins.print'):
                        main()

                        # Verify PingEnablementManager.process_vms was called correctly
                        mock_manager.process_vms.assert_called_once_with(vm_names=None, force_update=True)

def test_main_interactive_invalid_inputs():
    """Test main function handling invalid inputs in interactive mode."""
    from Enable_VM_Ping_Monitoring import main
    import scheduler

    # Mock argparse.ArgumentParser to return empty args (interactive mode)
    mock_args = MagicMock()
    mock_args.vm_name = None
    mock_args.all_vms = None
    mock_args.force = False
    mock_args.debug = False
    mock_args.command = None  # This is important

    with patch('Enable_VM_Ping_Monitoring.parse_arguments', return_value=mock_args):
        # Mock config loading
        mock_config = '{"operationsHost":"test.vcf.ops.com"}'
        with patch('builtins.open', mock_open(read_data=mock_config)):
            # Mock PingEnablementManager
            mock_manager = MagicMock()
            with patch('Enable_VM_Ping_Monitoring.PingEnablementManager', return_value=mock_manager):
                # Mock scheduler import and MonitoringScheduler
                mock_scheduler = MagicMock()
                mock_scheduler_class = MagicMock(return_value=mock_scheduler)
                with patch.dict('sys.modules', {'scheduler': scheduler}):
                    with patch('scheduler.MonitoringScheduler', mock_scheduler_class):
                        # Mock input responses for option 5 (invalid), then 1, with vm name 'test-vm'
                        # Note: Changed from 4 to 5 to avoid scheduler path
                        with patch('builtins.input', side_effect=['5', '1', 'test-vm', 'n']):
                            # Mock print to avoid output during test
                            with patch('builtins.print'):
                                main()

                                # Verify PingEnablementManager.process_vms was called correctly
                                mock_manager.process_vms.assert_called_once_with(vm_names=['test-vm'], force_update=False)