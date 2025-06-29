.PHONY: help setup dev test lint format clean docker-build docker-run docker-stop db-init db-start db-reset install-deps run-tests run-integration-tests run-performance-tests

# Python virtual environment
VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

# Default target
help:
	@echo "Buildship FastAPI - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  setup              - Complete project setup (creates venv, installs deps, starts DB, runs tests)"
	@echo "  install-deps       - Install Python dependencies in virtual environment"
	@echo "  db-start           - Start PostgreSQL and Redis databases"
	@echo "  db-init            - Initialize database tables (requires DB to be running)"
	@echo "  db-reset           - Reset database (drop and recreate tables)"
	@echo ""
	@echo "Development:"
	@echo "  dev                - Start development server with hot reload"
	@echo "  test               - Run all tests (unit + integration)"
	@echo "  run-tests          - Run unit tests only"
	@echo "  run-integration-tests - Run integration tests only"
	@echo "  run-performance-tests - Run k6 performance tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint               - Run linting checks"
	@echo "  format             - Format code with black and isort"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build       - Build Docker image"
	@echo "  docker-run         - Run application in Docker"
	@echo "  docker-stop        - Stop all Docker containers"
	@echo ""
	@echo "Cleaning:"
	@echo "  clean              - Clean up generated files and virtual environment"

# Setup virtual environment and install dependencies
setup:
	@echo "🚀 Setting up Buildship FastAPI development environment..."
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
	fi
	@echo "Installing dependencies..."
	@venv/bin/pip install --upgrade pip
	@venv/bin/pip install -r requirements.txt
	@echo "Starting database..."
	@$(MAKE) db-start
	@echo "Initializing database..."
	@$(MAKE) db-init
	@echo "Running tests..."
	@$(MAKE) test
	@echo "✅ Setup completed successfully!"

# Install dependencies
install-deps:
	@echo "Installing dependencies..."
	@venv/bin/pip install --upgrade pip
	@venv/bin/pip install -r requirements.txt

# Start database services
db-start:
	@echo "Starting PostgreSQL and Redis..."
	@docker-compose up -d postgres redis
	@echo "Waiting for database to be ready..."
	@sleep 15
	@echo "✅ Database services started"

# Initialize database tables
db-init:
	@echo "Initializing database tables..."
	@venv/bin/python -c "from app.database import init_db; init_db(); print('✅ Database tables created successfully!')"

# Reset database (drop and recreate tables)
db-reset:
	@echo "Resetting database..."
	@venv/bin/python -c "from app.database import reset_db; reset_db(); print('✅ Database reset successfully!')"

# Start development server
dev:
	@echo "Starting development server..."
	@venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run all tests
test:
	@echo "Running all tests..."
	@venv/bin/python -m pytest tests/ -v --tb=short

# Run unit tests only
run-tests:
	@echo "Running unit tests..."
	@venv/bin/python -m pytest tests/unit/ -v --tb=short

# Run integration tests only
run-integration-tests:
	@echo "Running integration tests..."
	@venv/bin/python -m pytest tests/integration/ -v --tb=short

# Run performance tests with k6
run-performance-tests:
	@echo "Running k6 performance tests..."
	@if command -v k6 > /dev/null 2>&1; then \
		echo "Running load test..."; \
		k6 run k6/performance-tests.js; \
		echo "Running stress test..."; \
		k6 run k6/stress-test.js; \
		echo "Running spike test..."; \
		k6 run k6/spike-test.js; \
	else \
		echo "❌ k6 not found. Please install k6 first:"; \
		echo "   macOS: brew install k6"; \
		echo "   Linux: sudo apt-get install k6"; \
		echo "   Windows: choco install k6"; \
		echo "   Or visit: https://k6.io/docs/getting-started/installation/"; \
	fi

# Run linting
lint:
	@echo "Running linting checks..."
	@venv/bin/flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	@venv/bin/mypy app/ --ignore-missing-imports

# Format code
format:
	@echo "Formatting code..."
	@venv/bin/black app/ tests/ --line-length=88
	@venv/bin/isort app/ tests/ --profile=black

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	@docker build -t buildship-fastapi .

# Run application in Docker
docker-run:
	@echo "Running application in Docker..."
	@docker-compose -f docker-compose.prod.yml up -d

# Stop all Docker containers
docker-stop:
	@echo "Stopping all Docker containers..."
	@docker-compose down
	@docker-compose -f docker-compose.prod.yml down

# Clean up
clean:
	@echo "Cleaning up..."
	@rm -rf venv/
	@rm -rf __pycache__/
	@rm -rf .pytest_cache/
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@echo "✅ Cleanup completed"

# Docker commands
docker-logs:
	docker-compose logs -f

# Production commands
docker-prod-build:
	docker build -t buildship-fastapi:prod .

docker-prod-run:
	docker-compose -f docker-compose.prod.yml up -d

docker-prod-stop:
	docker-compose -f docker-compose.prod.yml down

# Health check
health:
	curl -f http://localhost:8000/health || exit 1

# Combined test suite
test-all: test perf-test-dev
	@echo "All tests completed!"

# CI/CD commands
ci-test: venv
	$(PYTHON) -m pytest tests/ -v --cov=app --cov-report=xml --cov-report=term --junitxml=test-results.xml

ci-lint: venv
	$(VENV_DIR)/bin/flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	$(VENV_DIR)/bin/mypy app/ --ignore-missing-imports

ci-format-check: venv
	$(VENV_DIR)/bin/black --check app/ tests/
	$(VENV_DIR)/bin/isort --check-only app/ tests/

# Production setup
setup-prod: docker-prod-build docker-prod-run
	@echo "Production environment setup complete!" 