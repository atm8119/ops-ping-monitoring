#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run tests with coverage
pytest tests/ -v --cov=. --cov-report=term --cov-report=html

# Optional: Print report summary
echo ""
echo "Coverage report generated in htmlcov/ directory"
echo "Run 'open htmlcov/index.html' to view the full report"
