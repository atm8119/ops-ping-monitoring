# VCF Operations VM Ping Monitoring - Testing Guide

This guide provides information about the testing strategy for the VCF Operations VM Ping Monitoring tool, focusing on implementation details for developers maintaining the codebase.

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [Test Categories](#test-categories)
3. [Test Implementation](#test-implementation)
4. [Running Tests](#running-tests)
5. [Reviewing Test Results](#reviewing-test-results)
6. [Adding New Tests](#adding-new-tests)
7. [Test Coverage](#test-coverage)
8. [Continuous Integration](#continuous-integration)
9. [Scheduler Testing](#scheduler-testing)

## Testing Strategy

The testing strategy follows a progressive approach where tests build on each other, starting with basic functionality and moving to more complex scenarios. The key principles include:

- **Isolation**: Unit tests isolate individual components by mocking dependencies
- **Integration**: Integration tests verify components work together correctly
- **Coverage**: Tests aim to cover all code paths and edge cases
- **Automation**: Tests are automated and can be run as part of a CI pipeline
- **Maintenance**: Tests are structured for easy maintenance and extension

## Test Categories

### Unit Tests

- **Configuration Testing**: Verifies configuration loading and validation
- **Token Management**: Tests token fetching, storage, and refresh mechanisms
- **State Management**: Tests VM state tracking and caching functionality
- **API Calls**: Tests API request formation and response handling
- **Ping Enablement**: Tests the core ping enablement logic
- **Scheduler**: Tests schedule creation, state persistence, and user-friendly scheduling options

### Integration Tests

- **Component Integration**: Tests interaction between different components
- **API Integration**: Tests actual API calls (with mocked responses)
- **Workflow Integration**: Tests complete workflows from start to finish
- **Scheduler Integration**: Tests scheduler interaction with other components

### Interface Tests

- **CLI Testing**: Tests command-line interface functionality
- **Interactive Mode**: Tests interactive prompts and user input handling
- **Scheduler CLI**: Tests scheduler-specific CLI commands and options

### Error Handling Tests

- **API Errors**: Tests handling of various API error responses
- **Configuration Errors**: Tests handling of missing or invalid configuration
- **Network Errors**: Tests recovery from network connectivity issues
- **Input Errors**: Tests handling of invalid user input
- **Scheduler Errors**: Tests handling of invalid schedule configurations

## Test Implementation

All tests are implemented using pytest and are organized in the `tests/` directory. The implementation uses pytest fixtures for better reusability and maintenance.

### Key Files

```
tests/
├── conftest.py             # Shared fixtures
├── test_config.py          # Configuration tests
├── test_token.py           # Token management tests
├── test_state_management.py # State tracking tests
├── test_api_calls.py       # API interaction tests
├── test_ping_enablement.py # Core functionality tests
├── test_cli.py             # CLI tests
├── test_interactive.py     # Interactive mode tests
├── test_integration.py     # Integration tests
├── test_error_handling.py  # Error handling tests
└── test_scheduler.py       # Scheduler tests
```

### Essential Fixtures

The `conftest.py` file provides several key fixtures:

- `mock_ops_config`: Provides a standard test configuration
- `mock_vm_data`: Provides sample VM data for testing
- `mock_ping_enablement_manager`: Provides a pre-configured manager instance
- `temp_files`: Creates and cleans up temporary files for testing
- `mock_scheduler`: Provides a pre-configured scheduler instance

### Mocking Strategy

The tests use extensive mocking to isolate components:

```python
# Example of API call mocking
with patch.object(manager, '_make_request') as mock_request:
    mock_response = MagicMock()
    mock_response.json.return_value = mock_vm_data
    mock_request.return_value = mock_response

    vms = manager.get_all_vms()
    # Assertions...
```

## Running Tests

After installing development dependencies (`pip install -r requirements-dev.txt`):

### Running All Tests

```bash
./run_tests.sh
```

Or directly with pytest:

```bash
pytest tests/ -v --cov=. --cov-report=term --cov-report=html
```

### Running Specific Test Categories

```bash
pytest tests/test_config.py -v
pytest tests/test_token.py -v
pytest tests/test_scheduler.py -v
```

### Running Tests by Marker

```bash
pytest -m unit -v
pytest -m integration -v
pytest -m cli -v
pytest -m scheduler -v
```

## Reviewing Test Results

### Test Status

After running tests, pytest will display a summary showing:

- Total tests run
- Number of tests passed
- Number of tests failed
- Number of tests skipped

Example:
```
====== 35 passed, 2 skipped, 1 failed in 3.45s ======
```

### Test Coverage Report

The coverage report shows which parts of the code were executed during testing:

```bash
open htmlcov/index.html  # Open coverage report in browser
```

Key metrics to review:
- **Overall coverage percentage**: Aim for at least 80%
- **Module coverage**: Check coverage for individual modules
- **Missed lines**: Identify code paths not tested

## Adding New Tests

### Test Function Naming

Follow this naming convention:
```python
def test_<function_name>_<scenario>():
    # Test implementation
```

Example:
```python
def test_update_ping_enabled_when_already_enabled():
    # Test implementation
```

### Using Fixtures

Use fixtures from `conftest.py` to set up test prerequisites:

```python
def test_get_all_vms(mock_ping_enablement_manager, mock_vm_data):
    # Test implementation using fixtures
```

### Adding Markers

Add markers to categorize tests:

```python
@pytest.mark.unit
def test_simple_function():
    # Test implementation
```

## Test Coverage

### Coverage Goals

- **Overall code coverage**: Target 80%+ code coverage
- **Critical code paths**: Aim for 100% coverage of critical functionality
- **Error handling**: Test all error handling paths

### Improving Coverage

1. Identify untested code paths in the HTML report
2. Add tests targeting the specific untested functionality
3. Re-run coverage to verify improvement

## Continuous Integration

### Suggested CI Pipeline

1. **Setup**: Install dependencies
2. **Lint**: Run linting to check code quality
3. **Test**: Run all tests with coverage report
4. **Report**: Generate and publish test results

### GitHub Actions Example

```yaml
name: Test VCF Operations VM Ping Monitoring

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi

    - name: Test with pytest
      run: |
        pytest --junitxml=test-results.xml --cov=. --cov-report=xml

    - name: Upload test results
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: test-results.xml

    - name: Upload coverage report
      uses: actions/upload-artifact@v3
      with:
        name: coverage-report
        path: coverage.xml
```

## Scheduler Testing

The scheduler component has been enhanced with user-friendly scheduling options. When testing the scheduler, include the following test scenarios:

### Test Categories for Scheduler

- **User-Friendly Scheduling**:
  - Daily schedules with various times
  - Weekly schedules on different days
  - Monthly schedules on different days of the month
  - Interval schedules (minutes, hours, days)

- **Scheduler Control Flow**:
  - Starting the scheduler
  - Stopping the scheduler
  - Checking scheduler status
  - Running jobs immediately

- **Input Validation**:
  - Valid time formats (HH:MM)
  - Invalid time formats
  - Valid day of week specifications
  - Invalid day of week specifications
  - Valid interval values
  - Invalid interval values

### Example Test Cases

1. **Daily Schedule Tests**:
   - Set schedule to daily at midnight: `--daily`
   - Set schedule to daily at noon: `--daily 12:00`
   - Set schedule to daily at 3:45 PM: `--daily 15:45`
   - Invalid time format: `--daily 25:00`

2. **Weekly Schedule Tests**:
   - Set schedule to weekly on Sunday: `--weekly sun`
   - Set schedule to weekly on Monday at 9 AM: `--weekly mon 09:00`
   - Invalid day specification: `--weekly someday`

3. **Monthly Schedule Tests**:
   - Set schedule to monthly on the 1st: `--monthly 1`
   - Set schedule to monthly on the 15th at 6 PM: `--monthly 15 18:00`
   - Invalid day specification: `--monthly 32`

4. **Interval Schedule Tests**:
   - Set schedule to every 30 minutes: `--every 30 minutes`
   - Set schedule to every 6 hours: `--every 6 hours`
   - Set schedule to every 2 days: `--every 2 days`
   - Invalid interval: `--every 0 hours`
   - Invalid unit: `--every 5 seconds`

5. **Advanced Configuration Tests**:
   - Set target VMs: `--daily --target-vms vm1 vm2`
   - Set to process all VMs: `--daily --target-all-vms`
   - Set to use cache: `--daily --use-cache`
   - Set to ignore cache: `--daily --ignore-cache`

### Testing the Scheduler in Reality

When testing the scheduler in a real environment:

1. **Short Interval Testing**:
   - Configure a short interval (e.g., 2 minutes) for testing
   - Verify job executes at expected times
   - Check logs for proper execution

2. **Time-Based Testing**:
   - Set a specific time a few minutes in the future
   - Verify job executes at that time
   - Check status output shows correct next run time

3. **Persistence Testing**:
   - Configure scheduler
   - Stop and restart the scheduler
   - Verify configuration is preserved

4. **State Management Testing**:
   - Run a scheduled job
   - Verify state file is updated correctly
   - Ensure subsequent runs respect the cache setting

5. **Service Mode Testing**:
   - Install as a service
   - Start/stop via service manager
   - Verify runs persist across system reboots

### Automated Test Examples

The following are example tests for the scheduler functionality:

```python
def test_process_friendly_schedule_options_daily():
    """Test processing of --daily option."""
    # Create a mock args object
    args = MagicMock()
    args.daily = "08:30"
    args.weekly = None
    args.monthly = None
    args.every = None

    # Call the function
    updates = scheduler.process_friendly_schedule_options(args)

    # Verify results
    assert updates is not None
    assert updates['schedule_type'] == 'cron'
    assert updates['cron_expression'] == "30 8 * * *"

def test_human_readable_descriptions():
    """Test human readable schedule descriptions."""
    # Test daily patterns
    config = {
        "schedule_type": "cron",
        "cron_expression": "0 0 * * *"
    }
    assert "Daily at midnight" in scheduler.format_schedule_description(config)

    config["cron_expression"] = "0 12 * * *"
    assert "Daily at noon" in scheduler.format_schedule_description(config)
```

Run these tests with:

```bash
pytest tests/test_scheduler.py -v
```

For focused testing of specific functions:

```bash
pytest tests/test_scheduler.py::test_process_friendly_schedule_options_daily -v
pytest tests/test_scheduler.py::test_human_readable_descriptions -v
```

---

By implementing this testing strategy, you can ensure robust quality assurance for the VCF Operations VM Ping Monitoring tool, making it more reliable and maintainable.