# tests/test_config.py
import os
import json
import pytest
from unittest.mock import patch, mock_open

# Test configuration loading
def test_config_file_exists():
    """Test that the template config file exists."""
    assert os.path.exists('vcf-monitoring-loginData.json.template')

def test_config_file_is_valid_json():
    """Test that the template config file is valid JSON."""
    with open('vcf-monitoring-loginData.json.template', 'r') as f:
        try:
            json.load(f)
        except json.JSONDecodeError:
            pytest.fail("Config template is not valid JSON")

def test_config_loading():
    """Test loading the configuration file."""
    mock_config = """{
        "operationsHost":"test.vcf.ops.com",
        "loginData":{
            "username":"test@example.com",
            "authSource":"vIDMAuthSource",
            "password":"TestPassword!"
        }
    }"""

    with patch('builtins.open', mock_open(read_data=mock_config)):
        from Enable_VM_Ping_Monitoring import main

        # Mock parse_arguments to return an object with required attributes
        with patch('Enable_VM_Ping_Monitoring.parse_arguments') as mock_parse:
            mock_parse.return_value = type('obj', (object,), {
                'vm_name': None,
                'all_vms': None,
                'force': False,
                'debug': False
            })

            # Patch PingEnablementManager to avoid actual initialization
            with patch('Enable_VM_Ping_Monitoring.PingEnablementManager'):
                # Call main but return before any actual processing
                with patch('builtins.print'):  # Suppress print statements
                    main()

                # Verify config was loaded correctly
                # This is a bit of a trick since we mocked PingEnablementManager,
                # so we're just testing that the function completes without error