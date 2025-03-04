import pytest
from unittest.mock import patch, MagicMock, mock_open
import json
import sys
import os
import requests

import Fetch_New_Bearer_Token_VCF_Ops

def test_fetch_token_successful():
    """Test successful token fetching."""
    # Mock configuration
    mock_config = {
        "operationsHost": "test.vcf.ops.com",
        "loginData": {
            "username": "test@example.com",
            "authSource": "vIDMAuthSource",
            "password": "TestPassword!"
        }
    }

    # Mock response for the token request
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"token": "test-token-12345"}

    # Create a context manager that handles nested open calls correctly
    mock_file_data = {}
    mock_file_data[os.path.join(os.getcwd(), 'vcf-monitoring-loginData.json')] = json.dumps(mock_config)

    def mock_open_side_effect(filename, *args, **kwargs):
        if 'vcf-monitoring-loginData.json' in str(filename):
            return mock_open(read_data=json.dumps(mock_config))()
        return mock_open()()

    # Mock the requests.post call
    with patch('requests.post', return_value=mock_response):
        # Mock open with our side effect
        with patch('builtins.open', side_effect=mock_open_side_effect):
            # Mock os.getcwd
            with patch('os.getcwd', return_value=os.getcwd()):
                # Call the function
                Fetch_New_Bearer_Token_VCF_Ops.Fetch_New_Bearer_Token()

                # Verify requests.post was called
                # Uses a simpler assertion
                assert requests.post.called

def test_fetch_token_error():
    """Test error handling in token fetching."""
    # Mock configuration
    mock_config = {
        "operationsHost": "test.vcf.ops.com",
        "loginData": {
            "username": "test@example.com",
            "authSource": "vIDMAuthSource",
            "password": "TestPassword!"
        }
    }

    # Mock response for the token request with error
    mock_response = MagicMock()
    mock_response.status_code = 401

    def mock_open_side_effect(filename, *args, **kwargs):
        if 'vcf-monitoring-loginData.json' in str(filename):
            return mock_open(read_data=json.dumps(mock_config))()
        return mock_open()()

    # Use pytest.raises to catch the SystemExit
    with pytest.raises(SystemExit):
        with patch('requests.post', return_value=mock_response):
            with patch('builtins.open', side_effect=mock_open_side_effect):
                with patch('os.getcwd', return_value=os.getcwd()):
                    with patch('builtins.print'):
                        # Call the function which will exit
                        Fetch_New_Bearer_Token_VCF_Ops.Fetch_New_Bearer_Token()

def test_fetch_token_request_exception():
    """Test handling of request exceptions in token fetching."""
    # Mock configuration
    mock_config = {
        "operationsHost": "test.vcf.ops.com",
        "loginData": {
            "username": "test@example.com",
            "authSource": "vIDMAuthSource",
            "password": "TestPassword!"
        }
    }

    def mock_open_side_effect(filename, *args, **kwargs):
        if 'vcf-monitoring-loginData.json' in str(filename):
            return mock_open(read_data=json.dumps(mock_config))()
        return mock_open()()

    # Since we expect the test to handle the exception, we'll use pytest's raises
    with pytest.raises(requests.exceptions.RequestException):
        # Mock the requests.post call to raise an exception
        with patch('requests.post', side_effect=requests.exceptions.RequestException("Connection error")):
            # Mock open for reading config
            with patch('builtins.open', side_effect=mock_open_side_effect):
                # Mock os.getcwd
                with patch('os.getcwd', return_value=os.getcwd()):
                    # Call the function
                    Fetch_New_Bearer_Token_VCF_Ops.Fetch_New_Bearer_Token()