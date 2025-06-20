.PHONY: help install test lint format clean run docker-build docker-run docker-stop

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code with black"
	@echo "  clean       - Clean up cache and temporary files"
	@echo "  run         - Run the bot locally"
	@echo "  docker-build- Build Docker image"
	@echo "  docker-run  - Run bot in Docker"
	@echo "  docker-stop - Stop Docker containers"

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	python -m pytest tests/ -v

# Run linting
lint:
	flake8 src/
	mypy src/

# Format code
format:
	black src/

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/

# Run bot locally
run:
	python src/main.py

# Docker commands
docker-build:
	docker build -t commander-helper-bot .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

# Development setup
dev-setup: install format lint test

# Production setup
prod-setup: docker-build docker-run 