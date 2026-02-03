# Test Suite for AVBot

This directory contains a comprehensive test suite for the AVBot application. The tests are organized to cover all major components of the application and ensure proper functionality, error handling, and security.

## Test Organization

The test suite is organized into the following files:

1. `test_yandex_index_service.py` - Tests for the Yandex Index Service
2. `test_dialog_service.py` - Tests for the Dialog Service
3. `test_ics_client.py` - Tests for the ICS Client
4. `test_ics_handler.py` - Tests for the ICS Handler
5. `test_bot_handlers.py` - Integration tests for bot handlers
6. `conftest.py` - pytest configuration and shared fixtures


## Running the Tests

To run the tests, you'll need to have the required dependencies installed. From the project root directory, you can run:

```bash
# Run all tests
pytest tests/

# Run a specific test file
pytest tests/test_yandex_index_service.py

# Run tests with coverage report
pytest --cov=services --cov=clients --cov=handlers tests/

# Run tests in verbose mode
pytest -v tests/
```

## Test Dependencies

The tests require the following Python packages:
- pytest
- pytest-asyncio
- pytest-cov (for coverage reports)
- python-telegram-bot
- requests
- pydub
- speechkit

These can be installed with:
```bash
pip install pytest pytest-asyncio pytest-cov python-telegram-bot requests pydub speechkit
```

## Test Structure

Each test file follows a consistent structure:

1. Import necessary modules and add the project root to the Python path
2. Define test classes for each component being tested
3. Use pytest fixtures for setup and teardown
4. Include tests for normal operation, edge cases, and error conditions
5. Use mocking to isolate units under test
6. Follow pytest naming conventions (test_* for functions, Test* for classes)

## Writing New Tests

When adding new tests, follow these guidelines:

1. Create a new test file for each major component
2. Use descriptive test function names that explain what is being tested
3. Include tests for both success and failure cases
4. Use appropriate mocking to isolate the unit under test
5. Follow the existing patterns in the test suite
6. Add any new dependencies to the requirements.txt file

## Continuous Integration

The test suite is integrated with GitHub Actions for continuous integration. The workflow is defined in `.github/workflows/ci.yml` and will automatically run the tests on each push to the repository.

## Coverage

The test suite aims for comprehensive coverage of the application code, including:

- All public methods and functions
- Error handling paths
- Edge cases and boundary conditions
- Integration points between components
- Security-sensitive code paths

## Maintaining the Test Suite

To keep the test suite up-to-date:

1. Add new tests when adding new features
2. Update existing tests when modifying existing code
3. Regularly run the full test suite to ensure all tests pass
4. Monitor coverage reports to identify untested code paths
5. Review and update tests when dependencies change