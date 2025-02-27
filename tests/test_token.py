# tests/test_token.py
import pytest
from unittest.mock import patch, MagicMock, mock_open

# Test token handling
def test_get_bearer_token_from_file():
    """Test loading bearer token from file."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager

    # Mock file opening and reading
    mock_token = "test-token-12345"
    with patch('builtins.open', mock_open(read_data=mock_token)):
        # Create a PingEnablementManager with minimal mocking
        with patch.object(PingEnablementManager, '_load_state', return_value={}):
            manager = PingEnablementManager("test.vcf.ops.com")

            # Access the token directly (normally not good practice but needed for test)
            assert manager.bearer_token == "test-token-12345"

def test_get_bearer_token_refresh():
    """Test refreshing bearer token when file not found."""
    from Enable_VM_Ping_Monitoring import PingEnablementManager
    import Fetch_New_Bearer_Token_VCF_Ops

    # Mock the fetch token function
    with patch.object(Fetch_New_Bearer_Token_VCF_Ops, 'Fetch_New_Bearer_Token'):
        # Mock the file not found on first try, then found on second try
        mock_file_missing = MagicMock(side_effect=[FileNotFoundError, mock_open(read_data="new-token-67890").return_value])

        with patch('builtins.open', mock_file_missing):
            with patch.object(PingEnablementManager, '_load_state', return_value={}):
                manager = PingEnablementManager("test.vcf.ops.com")
                assert manager.bearer_token == "new-token-67890"

                # Verify that Fetch_New_Bearer_Token was called
                Fetch_New_Bearer_Token_VCF_Ops.Fetch_New_Bearer_Token.assert_called_once()
