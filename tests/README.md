# VCF Operations VM Ping Monitoring - Tests

This directory contains tests for the VCF Operations VM Ping Monitoring tool.

## Test Structure

Tests are organized into the following categories:

1. **Configuration Tests** (`test_config.py`)
   - Testing configuration loading and validation

2. **Token Tests** (`test_token.py`)
   - Testing token fetching and refreshing

3. **State Management Tests** (`test_state_management.py`)
   - Testing VM state tracking and caching

4. **API Call Tests** (`test_api_calls.py`)
   - Testing API interactions with VCF Operations

5. **Ping Enablement Tests** (`test_ping_enablement.py`)
   - Testing the core ping enablement functionality

6. **CLI Tests** (`test_cli.py`)
   - Testing command-line interface functionality

7. **Interactive Mode Tests** (`test_interactive.py`)
   - Testing interactive user input handling

8. **Integration Tests** (`test_integration.py`)
   - Testing integration between components

9. **Error Handling Tests** (`test_error_handling.py`)
   - Testing error conditions and recovery

## Running Tests

To run all tests:

```bash
./run_tests.sh
```

To run specific test categories:

```bash
pytest tests/test_config.py -v
pytest tests/test_token.py -v
```

To run tests by marker:

```bash
pytest -m unit -v
pytest -m integration -v
pytest -m cli -v
```

## Test Coverage

Test coverage reports are generated in HTML form in the `htmlcov/` directory.
Open `htmlcov/index.html` in a browser to view the coverage report.

## Adding New Tests

When adding new tests:

1. Place them in the appropriate test file by category
2. Follow the naming convention: `test_<function_name>_<scenario>`
3. Use fixtures from `conftest.py` where applicable
4. Add appropriate markers to categorize the test
