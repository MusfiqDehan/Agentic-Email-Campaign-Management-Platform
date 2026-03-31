Run the backend test suite for this project.

Navigate to the backend and run: `pytest $ARGUMENTS --tb=short -v`
- No arguments: runs all tests
- Specific file: `pytest apps/campaigns/tests/test_email_logs.py -v`
- With coverage: `pytest --cov=apps --cov-report=term-missing`

Working directory: `/home/musfiqdehan/Products/Email-Campaign-Management-Platform/backend`
