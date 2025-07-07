.PHONY: help setup dev test lint format clean docker-build docker-run docker-stop db-init db-start db-reset install-deps run-tests run-integration-tests run-performance-tests docker-push docker-deploy version

# Python virtual environment
VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

# Get version from git tags or default to dev
VERSION ?= $(shell git describe --tags --abbrev=0 2>/dev/null || echo "dev")
MAJOR_MINOR ?= $(shell git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//' | sed 's/\.[0-9]*$$//' || echo "dev")
GIT_COMMIT = $(shell git rev-parse --short HEAD)
GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)
REGISTRY = ghcr.io
REPO_NAME = $(shell git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\)\/\([^/]*\).*/\1\/\2/' | sed 's/\.git$$//')
IMAGE_NAME = $(REGISTRY)/$(REPO_NAME)

# Default target
help:
	@echo "Buildship FastAPI - Available Commands:"
	@echo ""
	@echo "Version Management:"
	@echo "  version            - Show current version information"
	@echo "  docker-build       - Build Docker image locally with version"
	@echo "  docker-push        - Build and push Docker image to registry with version"
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
	@echo "  test-coverage      - Run tests with coverage report"
	@echo "  run-tests          - Run unit tests only"
	@echo "  run-integration-tests - Run integration tests only"
	@echo "  run-performance-tests - Run k6 performance tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint               - Run linting checks"
	@echo "  format             - Format code with black and isort"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build       - Build Docker image locally with version"
	@echo "  docker-push        - Build and push Docker image to registry with version"
	@echo "  docker-run         - Run application in Docker"
	@echo "  docker-deploy      - Deploy to production using docker-compose.prod.yml"
	@echo "  docker-stop        - Stop all Docker containers"
	@echo ""
	@echo "Cleaning:"
	@echo "  clean              - Clean up generated files and virtual environment"

# Show version information
version:
	@echo "Version Information:"
	@echo "  Full Version: $(VERSION)"
	@echo "  Major.Minor: $(MAJOR_MINOR)"
	@echo "  Git Commit: $(GIT_COMMIT)"
	@echo "  Git Branch: $(GIT_BRANCH)"
	@echo "  Registry: $(REGISTRY)"
	@echo "  Repository: $(REPO_NAME)"
	@echo "  Image Name: $(IMAGE_NAME)"

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

# Run tests with coverage
test-coverage:
	@echo "Running tests with coverage report..."
	@venv/bin/python -m pytest --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=90 tests/

# Run unit tests only
run-tests:
	@echo "Running unit tests..."
	@venv/bin/python -m pytest tests/unit/ -v --tb=short

# Run integration tests only
run-integration-tests:
	@echo "Running integration tests..."
	@venv/bin/python -m pytest tests/integration/ -v --tb=short

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

# Build Docker image locally with version
docker-build:
	@echo "Building Docker image $(IMAGE_NAME):$(MAJOR_MINOR)..."
	@docker build -t $(IMAGE_NAME):$(MAJOR_MINOR) .
	@docker tag $(IMAGE_NAME):$(MAJOR_MINOR) $(IMAGE_NAME):latest
	@echo "✅ Built $(IMAGE_NAME):$(MAJOR_MINOR) and $(IMAGE_NAME):latest"

# Build and push Docker image to registry with version
docker-push:
	@echo "Building and pushing Docker image $(IMAGE_NAME):$(MAJOR_MINOR)..."
	@docker build -t $(IMAGE_NAME):$(MAJOR_MINOR) .
	@docker tag $(IMAGE_NAME):$(MAJOR_MINOR) $(IMAGE_NAME):latest
	@docker push $(IMAGE_NAME):$(MAJOR_MINOR)
	@docker push $(IMAGE_NAME):latest
	@echo "✅ Pushed $(IMAGE_NAME):$(MAJOR_MINOR) and $(IMAGE_NAME):latest"

# Run application in Docker
docker-run:
	@echo "Running application in Docker..."
	@docker-compose -f docker-compose.prod.yml up -d

# Deploy to production
docker-deploy:
	@echo "Deploying to production..."
	@docker-compose -f docker-compose.prod.yml up -d --force-recreate

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